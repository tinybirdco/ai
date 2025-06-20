import { LanguageModelV1, LanguageModelV1CallOptions } from "@ai-sdk/provider";

type TinybirdWrapperSettings = {
  token: string;
  host: string;

  organization?: string | undefined;
  project?: string | undefined;
  environment?: string | undefined;

  chatId?: string | undefined;
  user?: string | undefined;
  event?: string | undefined;
};

type AsyncReturnType<T extends (...args: any) => PromiseLike<any>> = T extends (
  ...args: any
) => PromiseLike<infer R>
  ? R
  : any;

/**
 * Wraps a model from Vercel's AI SDK to add Tinybird analytics and logging.
 * This wrapper is specifically designed to work with Vercel's AI SDK models and adds
 * Tinybird event tracking for monitoring and analytics purposes.
 *
 * @param model - The model instance from Vercel's AI SDK
 * @param settings - Configuration for Tinybird analytics and logging
 * @returns The wrapped model with Tinybird analytics capabilities
 */
export function wrapModel(
  model: LanguageModelV1,
  settings: TinybirdWrapperSettings
) {
  const _doGenerate = model.doGenerate;
  const _doStream = model.doStream;

  function composeTinybirdEvent(
    model: LanguageModelV1,
    startTime: Date,
    status: "success" | "error",
    result: AsyncReturnType<LanguageModelV1["doGenerate"]> | undefined,
    error: Error | undefined,
    args: [options: LanguageModelV1CallOptions]
  ) {
    const id = crypto.randomUUID();
    const endTime = new Date();

    const duration = endTime.getTime() - startTime.getTime();

    const composeResponse = (
      result: AsyncReturnType<LanguageModelV1["doGenerate"]> | undefined
    ) => {
      return {
        id,
        object: "chat.completion",
        usage: {
          prompt_tokens: result?.usage?.promptTokens || 0,
          completion_tokens: result?.usage?.completionTokens || 0,
          total_tokens:
            (result?.usage?.promptTokens || 0) +
            (result?.usage?.completionTokens || 0),
        },
        choices: [{ message: { content: result?.text ?? "" } }],
      };
    };

    const composeMessages = (args: [options: LanguageModelV1CallOptions]) => {
      return args[0]?.prompt
        ? [{ role: "user", content: args[0].prompt }].map((m) => ({
            role: String(m.role),
            content: String(m.content),
          }))
        : [];
    };

    return {
      id,
      message_id: id,

      model: model.modelId || "unknown",
      provider: model.provider || "unknown",

      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      duration,
      llm_api_duration_ms: duration,

      response: composeResponse(result),
      messages: composeMessages(args),

      proxy_metadata: {
        organization: settings.organization || "",
        project: settings.project || "",
        environment: settings.environment || "",
        chat_id: settings.chatId || "",
      },

      user: settings.user || "unknown",
      standard_logging_object_status: status,
      standard_logging_object_response_time: duration,
      log_event_type: settings.event || "chat_completion",
      call_type: "completion",
      cache_hit: false,

      ...(status === "error" && {
        exception: error?.message || "Unknown error",
        traceback: error?.stack || "",
      }),
    };
  }

  async function logToTinybird(event: ReturnType<typeof composeTinybirdEvent>) {
    try {
      const res = await fetch(settings.host + `/v0/events?name=llm_events`, {
        method: "POST",
        body: JSON.stringify(event),
        headers: {
          Authorization: `Bearer ${settings.token}`,
          "Content-Type": "application/json",
        },
      });

      const data = await res.text();
      console.log("data", data);
    } catch (error) {
      console.error(error);
    }
  }

  model.doGenerate = async function (...args) {
    const startTime = new Date();

    try {
      const result = await _doGenerate.apply(this, args);
      await logToTinybird(
        composeTinybirdEvent(
          model,
          startTime,
          "success",
          result,
          undefined,
          args
        )
      );
      return result;
    } catch (error) {
      await logToTinybird(
        composeTinybirdEvent(
          model,
          startTime,
          "error",
          undefined,
          error as Error,
          args
        )
      );
      throw error;
    }
  };

  model.doStream = async function (...args) {
    const startTime = new Date();

    try {
      const result = await _doStream.apply(this, args);
      await logToTinybird(
        composeTinybirdEvent(
          model,
          startTime,
          "success",
          undefined,
          undefined,
          args
        )
      );
      return result;
    } catch (error) {
      await logToTinybird(
        composeTinybirdEvent(
          model,
          startTime,
          "error",
          undefined,
          error as Error,
          args
        )
      );
      throw error;
    }
  };

  return model;
}

export function wrapOpenai(...args: Parameters<typeof wrapModel>) {
  return wrapModel(...args)
}