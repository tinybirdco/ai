Step 1: Collect data

      - `execute_query` select now() to get the current date.
      - `report_date` is defined by the user
      - `comparison_date` is the previous beriod

      - **MCP Tool Usage Data (`report_date`):**
        - Query `tinybird.pipe_stats_rt` to get total requests, total errors, average latency (ms), p90, p95, p99 latencies
      (ms), and total read bytes for pipes where `url` contains 'from=mcp'.
        - Aggregate data by `pipe_name`.
        - Order by `total_requests` in descending order and limit to the top 15 pipes.
        - The `start_datetime` filter should be `start_datetime >= toDateTime('{report_date} 00:00:00') AND start_datetime
      < toDateTime('{report_date} 23:59:59')`. If data is empty for `23:59:59`, retry with `start_datetime <
      toDateTime('{report_date_plus_1_day} 00:00:00')`.
        - Query:
          ```sql
          SELECT
              pipe_name,
              count() AS total_requests,
              sum(error) AS total_errors,
              avg(duration) AS avg_latency_ms,
              quantile(0.9)(duration) AS p90_latency_ms,
              quantile(0.95)(duration) AS p95_latency_ms,
              quantile(0.99)(duration) AS p99_latency_ms,
              sum(read_bytes) AS total_read_bytes
          FROM tinybird.pipe_stats_rt
          WHERE start_datetime >= toDateTime('{report_date} 00:00:00') AND start_datetime <
      toDateTime('{report_date_plus_1_day} 00:00:00')
            AND url LIKE '%from=mcp%'
          GROUP BY pipe_name
          ORDER BY total_requests DESC
          LIMIT 15
          ```

      - **Comparison Day MCP Tool Usage Data (`comparison_date`):**
        - Execute the same query as above, but for `comparison_date`.
        - The `start_datetime` filter should be `start_datetime >= toDateTime('{comparison_date} 00:00:00') AND
      start_datetime < toDateTime('{comparison_date_plus_1_day} 00:00:00')`.
        - Query:
          ```sql
          SELECT
              pipe_name,
              count() AS total_requests,
              sum(error) AS total_errors,
              avg(duration) AS avg_latency_ms,
              quantile(0.9)(duration) AS p90_latency_ms,
              quantile(0.95)(duration) AS p95_latency_ms,
              quantile(0.99)(duration) AS p99_latency_ms,
              sum(read_bytes) AS total_read_bytes
          FROM tinybird.pipe_stats_rt
          WHERE start_datetime >= toDateTime('{comparison_date} 00:00:00') AND start_datetime <
      toDateTime('{comparison_date_plus_1_day} 00:00:00')
            AND url LIKE '%from=mcp%'
          GROUP BY pipe_name
          ORDER BY total_requests DESC
          LIMIT 15
          ```

      - **Parameter Breakdown (`report_date`):**
        - Query `tinybird.pipe_stats_rt` to get the top 15 most frequently used parameter keys.
        - Filter by `url LIKE '%from=mcp%'` and the `report_date`.
        - Query:
          ```sql
          SELECT
              key,
              pipe_name,
              count() AS usage_count
          FROM tinybird.pipe_stats_rt
          ARRAY JOIN mapKeys(parameters) AS key
          WHERE start_datetime >= toDateTime('{report_date} 00:00:00') AND start_datetime <
      toDateTime('{report_date_plus_1_day} 00:00:00')
            AND url LIKE '%from=mcp%'
          GROUP BY key, pipe_name
          ORDER BY usage_count DESC
          LIMIT 15
          ```

      - **Comparison Day Parameter Breakdown (`comparison_date`):**
        - Execute the same query as above, but for `comparison_date`.
        - Query:
          ```sql
          SELECT
              key,
              pipe_name,
              count() AS usage_count
          FROM tinybird.pipe_stats_rt
          ARRAY JOIN mapKeys(parameters) AS key
          WHERE start_datetime >= toDateTime('{comparison_date} 00:00:00') AND start_datetime <
      toDateTime('{comparison_date_plus_1_day} 00:00:00')
            AND url LIKE '%from=mcp%'
          GROUP BY key, pipe_name
          ORDER BY usage_count DESC
          LIMIT 15
          ```

      - **Error Handling:** If any query returns empty data, the agent should try to identify potential issues (e.g.,
      incorrect date format, no data for the specific day) and retry with slightly adjusted date ranges (e.g., widen the
      time window by an hour or two) if it suspects a data ingestion delay. If still no data, report it as such.

      Step 2: Analyze the data

      - For both the day and comparison day data:
        - Calculate the total number of requests across all pipes.
        - Calculate the total number of errors across all pipes.
        - Identify the top 10 pipes by total requests.
        - Identify the top 10 pipes by total errors.
        - Identify the top 10 pipes by average latency.
        - Identify the top 10 common parameter keys and their usage counts.
      - Compare the day's metrics with the comparison day's metrics.
        - Calculate Day-over-Day (DoD) growth/decline for:
          - Total requests
          - Total errors
          - Average latency (overall or for top pipes)
          - Total read bytes
        - Highlight any significant anomalies (e.g., sudden spikes or drops) in requests, errors, or latency.
        - Analyze the parameter breakdown to see if any new or unusually frequent parameters appeared.

      Step 3: Build report:
      The report needs to be structured. Add 3 to 4 main topics as a numbered list.

      Each topic MUST be drilled down to specific metrics that's explanatory. Use bulleted list with 2 to 4 elements.

      All ranks and lists need to be bulleted.

      Use link notation only if it makes sense, it MUST to be actual absolute URLs related to the insight. Do not use link
      notation if it's not an actual link

      1.  *Daily MCP Tool Usage Overview (Date: {report_date}):* A summary of the overall MCP tool usage, including total
      requests, total errors, and average latency for the day. Highlight any major changes compared to the previous day.
          *   *Total Requests:* {total_requests_day} (DoD: {total_requests_dod_change}%)
          *   *Total Errors:* {total_errors_day} (DoD: {total_errors_dod_change}%)
          *   *Average Latency:* {avg_latency_day}ms (DoD: {avg_latency_dod_change}%)
          *   *Total Data Read:* {total_read_bytes_day} (DoD: {total_read_bytes_dod_change}%)

      2.  *Top 10 Pipes by Usage and Performance:* Detailed breakdown of the most active and performant pipes. Identify any
      pipes with significant changes in requests, errors, or latency.
          *   *Top 10 Pipes by Requests:*
              *   {pipe_name_1}: {requests_1} requests, {errors_1} errors, {avg_latency_1}ms avg latency, {read_bytes_1}
      read
              *   ... (up to 10 pipes)
          *   *Top 10 Pipes by Errors:*
              *   {pipe_name_error_1}: {errors_error_1} errors, {requests_error_1} requests
              *   ... (up to 10 pipes)
          *   *Top 10 Pipes by Latency (P95):*
              *   {pipe_name_latency_1}: {p95_latency_1}ms P95 latency, {requests_latency_1} requests
              *   ... (up to 10 pipes)

      3.  *Parameter Usage Breakdown:* Insights into the most commonly used parameters in MCP tool requests.
          *   *Top 10 Parameter Keys:*
              *   `{parameter_key_1}`: {usage_count_1} usages
              *   ... (up to 10 parameter keys)
          *   Analyze any unusual spikes in parameter usage, potentially indicating new feature adoption or issues.

      Actionable insights summary in two to three sentences. Include corrective measures, experiments the user can run,
      suggest further explorations. For example, investigate pipes with high error rates or sudden latency spikes. Consider
      optimizing queries for pipes with high read bytes.

      Indicate in the report the tool calls made with the different parameters, time ranges, etc.
      Example:
      - Query 1: `SELECT ... FROM tinybird.pipe_stats_rt WHERE start_datetime >= toDateTime('{report_date} 00:00:00') AND
      start_datetime < toDateTime('{report_date_plus_1_day} 00:00:00') AND url LIKE '%from=mcp%' GROUP BY pipe_name ORDER
      BY total_requests DESC LIMIT 15`

      Format bytes in GB, TB, PB, etc.
      Format numbers in K, M, B, etc.

      Step 4: Send to Slack
      - The report is going to be printed in a Slack channel with plaintext format.
      - Wrap titles into * for bold text
      - Use this format <url|title (replies)> for links
      - Sort by metric1, then by metric2, then by metric3, then by metric4.