Your goal is to correlate cpu usage spikes with other metrics to understand the root cause. DO NOT PROVIDE A FINAL RESPONSE UNTIL ALL PLANNED STEPS ARE EXECUTED.

DO NOT USE text_to_sql tool.

<cpu_usage_spikes_steps>
Investigation Plan: CPU Usage Spike Analysis

1. Find CPU Usage Spikes timeframes
- Use the explore_data tool to find the timeframe of the spike with the following instructions
- Datasource: organization.metrics_logs
- Metric: metric='LoadAverage1'
- Analysis: Calculate the maximum load per minute
- Threshold: Load average greater than 60 (spike indicator)
- Priority: If multiple spikes exist, select the most relevant one
- Output: extract the timeframe expanded to several minutes that include the spike, list of workspace_ids, workspace_names from `organization.workspaces` filtering by organization_id if available. Use them to filter in next steps

2. Correlate and Find Root Causes
Once the spike timeframe is identified, investigate other metrics from the following datasources within the same timeframe:
- `organization.datasource_metrics_by_minute`
- `organization.pipe_metrics_by_minute`
- `organization.jobs_log`

Metrics collection:
- Requests Analysis (organization.pipe_metrics_by_minute):
  - Collect all metrics from the pipe_metrics_by_minute datasource
  - Filter by `minute_interval` for the spike timeframe in the previous step and filter by `workspace_id` if available
  
- Ingestion Analysis (organization.datasource_metrics_by_minute):
  - Collect all metrics from the datasource_metrics_by_minute datasource
  - Filter by `minute_interval` for the spike timeframe in the previous step and filter by `workspace_id` if available
  
- Job Analysis (organization.jobs_log):
  - Collect all metrics from the jobs_log datasource
  - Filter by `started_at` for the spike timeframe in the previous step and filter by `workspace_id` if available

Anomalies to investigate:
- Compare metrics during the spike calculated from previous step with the hour before the spike
- Use appropriate statistical methods to identify anomalies
- Use appropriate timeframes to calculate baselines and anomalies
- Establish baseline to identify anomalies
- Get correlations between metrics to understand the root cause
- Root cause indicators:
  - Timeout errors (408), rate limited requests (429) and cluster errors (5xx) indicate culprits
  - Concurrent operations
  - High number of jobs
  - High cpu_time or memory_usage

You MUST report the workspace names in the summary, filter organization.workspaces by workspace_id to get the workspace names

3. Summarize and Notify
- Summarize investigation findings
- You MUST send a structured slack message
- You MUST include all relevant quantitative metrics and a timeframe (start, end) around the spike
- See example message below but it's not complete, you MUST include all relevant metrics and workspaces
<slack_example_message>
  Summary:
    - A CPU spike was detected between 2025-06-10 05:33:00 and 2025-06-10 05:34:00 with a max load of 87.8 (threshold: 60).
    - Root Cause: High traffic to the query_api pipe in the {workspace_name} workspace.
    - Also, a large number of sink jobs were running in the {workspace_name}, {workspace_name_2} workspaces during the same timeframe.

  Relevant quantitative metrics:
    - 10 timeout errors were detected in the query_api pipe
    - average duration of requests to the query_api pipe was 1.2 seconds, max 3.4 seconds compared to 0.5 seconds, 1.8 seconds in the previous hour

  Workspaces Impacted:
    - {workspace_name}

  Pipes and Datasources Impacted:
    - {workspace_name}: query_api
    - {workspace_name}: datasource_a

  Recommendations:
    - Monitor the traffic to the query_api pipe and the duration of sink jobs.
    - Consider optimizing the queries executed through the query_api pipe.

  Severity:
    - Medium
</slack_example_message>
<slack_message_instructions>
- Use backticks and Slack formatting for names, tables and code blocks.
- Open a slack thread with the user to continue the investigation asking concisely for follow up questions or to run new queries.
- Send just one message to the channel and one to the thread.
</slack_message_instructions>
</cpu_usage_spikes_steps>