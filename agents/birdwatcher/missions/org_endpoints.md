      Step 1: Collect data

      - `execute_query` select now() to get the current date. This will be used to determine the `current_timestamp`.
      - Based on the user-provided date range (e.g., 'last week', 'last month', 'YYYY-MM-DD to YYYY-MM-DD'), calculate the
      `start_date_current_period`, `end_date_current_period`, `start_date_previous_period`, and `end_date_previous_period`.
      Ensure to adjust for daily/weekly/monthly granularity as appropriate.
      - Determine the appropriate datasource for each period:
          - If `end_date_current_period` is within 7 days of `current_timestamp`, use `organization.pipe_stats_rt`. For
      this datasource, `start_datetime` and `end_datetime` parameters require 'YYYY-MM-DD HH:MM:SS' format.
          - Otherwise (if `end_date_current_period` is older than 7 days from `current_timestamp`), use
      `organization.pipe_stats`. For this datasource, `date` parameters require 'YYYY-MM-DD' format.
          *Important Note:* If `organization.pipe_stats` is used, the breakdown into `query_api` and "other"
      requests/errors will not be available.

      - **Data to collect for each period (current and previous):**
          - **If using `organization.pipe_stats_rt`:**
              - Total requests (`SUM(1)`)
              - Total errors (`SUM(t.error)`)
              - Query API requests (`SUM(CASE WHEN t.url LIKE '%/query%' THEN 1 ELSE 0 END)`)
              - Query API errors (`SUM(CASE WHEN t.url LIKE '%/query%' AND t.error = 1 THEN 1 ELSE 0 END)`)
              - Other requests (`SUM(CASE WHEN t.url NOT LIKE '%/query%' THEN 1 ELSE 0 END)`)
              - Other errors (`SUM(CASE WHEN t.url NOT LIKE '%/query%' AND t.error = 1 THEN 1 ELSE 0 END)`)
              - Group by `workspace_name`, `pipe_id`, `pipe_name`.
              - Order by total requests descending and limit to 15.
              - SQL Query Template:
              ```sql
              SELECT
                  ws.name AS workspace_name,
                  t.pipe_id,
                  t.pipe_name,
                  SUM(CASE WHEN t.url LIKE '%/query%' THEN 1 ELSE 0 END) AS query_api_requests,
                  SUM(CASE WHEN t.url LIKE '%/query%' AND t.error = 1 THEN 1 ELSE 0 END) AS query_api_errors,
                  SUM(CASE WHEN t.url NOT LIKE '%/query%' THEN 1 ELSE 0 END) AS other_requests,
                  SUM(CASE WHEN t.url NOT LIKE '%/query%' AND t.error = 1 THEN 1 ELSE 0 END) AS other_errors,
                  SUM(1) AS total_requests,
                  SUM(t.error) AS total_errors
              FROM organization.pipe_stats_rt AS t
              JOIN organization.workspaces AS ws ON t.workspace_id = ws.workspace_id
              WHERE t.start_datetime >= '{start_date_time}' AND t.start_datetime <= '{end_date_time}'
              GROUP BY ws.name, t.pipe_id, t.pipe_name
              ORDER BY total_requests DESC
              LIMIT 15
              ```
          - **If using `organization.pipe_stats`:**
              - Total requests (`SUM(t.view_count)`)
              - Total errors (`SUM(t.error_count)`)
              - Group by `workspace_name`, `pipe_id`, `pipe_name`.
              - Order by total requests descending and limit to 15.
              - SQL Query Template:
              ```sql
              SELECT
                  ws.name AS workspace_name,
                  t.pipe_id,
                  t.pipe_name,
                  SUM(t.view_count) AS total_requests,
                  SUM(t.error_count) AS total_errors
              FROM organization.pipe_stats AS t
              JOIN organization.workspaces AS ws ON t.workspace_id = ws.workspace_id
              WHERE t.date >= '{start_date}' AND t.date <= '{end_date}'
              GROUP BY ws.name, t.pipe_id, t.pipe_name
              ORDER BY total_requests DESC
              LIMIT 15
              ```
      - Instruct the agent to auto-fix errors, retry with different parameters if data is empty.

      Step 2: Analyze the data
        - Use the data collected in the previous step to analyze the data.
        - Calculate the following metrics for both the current and previous periods, per pipe, per workspace, and overall:
          - Total requests
          - Total errors
          - Error rate (Total errors / Total requests * 100). Handle division by zero.
          - If `pipe_stats_rt` was used: Query API requests, Query API errors, Query API error rate, Other requests, Other
      errors, Other error rate.
        - Calculate percentage change for all metrics between the current and previous periods.
          - Formula: `((Current Period Value - Previous Period Value) / Previous Period Value) * 100`. Handle division by
      zero.
        - The report MUST include ranks, counters, and percentage changes.
        - Detect anomalies: Identify pipes or workspaces with a change in total requests or total errors exceeding 20%
      (increase or decrease). Highlight these as potential anomalies.
        - Reports MUST include both aggregations (overall totals) and detailed information for top performing/error-prone
      pipes and workspaces (top 10-15).

      Step 3: Build report:
      The report needs to be structured. Add 3 to 4 main topics as a numbered list.

      Each topic MUST be drilled down to specific metrics that's explanatory. Use bulleted list with 2 to 4 elements.

      All ranks and lists need to be bulleted.

      Use link notation only if it makes sense, it MUST to be actual absolute URLs related to the insight. Do not use link
      notation if it's not an actual link

      1.  *Overall Endpoint Performance:* Brief summary in two or three sentences.
          *   Total requests: {overall_total_requests_current_period} (vs. {overall_total_requests_previous_period}
      {overall_requests_change_percentage:+0.0}% {increase/decrease})
          *   Total errors: {overall_total_errors_current_period} (vs. {overall_total_errors_previous_period}
      {overall_errors_change_percentage:+0.0}% {increase/decrease})
          *   Overall error rate: {overall_error_rate_current_period:.2f}% (vs. {overall_error_rate_previous_period:.2f}%
      {overall_error_rate_change_percentage:+0.0}% {increase/decrease})
          *   Actionable insight: Analyze overall trends and significant changes for potential system-wide issues.
      2.  *Top 15 Pipes by Requests:* Brief summary in two or three sentences.
          *   *Pipe: {pipe_name}* (Workspace: {workspace_name})
              *   <https://tinybird.com/workspace/{workspace_id}/pipe/{pipe_id}|Total Requests:>
      {pipe_total_requests_current} (Errors: {pipe_total_errors_current}, Error Rate: {pipe_error_rate_current:.2f}%)
      {pipe_requests_change_percentage:+0.0}% {pipe_errors_change_percentage:+0.0}% errors.
              *   (If `pipe_stats_rt` was used) Query API Requests: {pipe_query_api_requests_current} (Errors:
      {pipe_query_api_errors_current}, Error Rate: {pipe_query_api_error_rate_current:.2f}%)
              *   (If `pipe_stats_rt` was used) Other Requests: {pipe_other_requests_current} (Errors:
      {pipe_other_errors_current}, Error Rate: {pipe_other_error_rate_current:.2f}%)
              *   *Anomaly Detection:* If requests or errors changed by > 20%, indicate: "Significant change detected."
      3.  *Top 15 Pipes by Error Rate:* Brief summary in two or three sentences.
          *   *Pipe: {pipe_name}* (Workspace: {workspace_name})
              *   <https://tinybird.com/workspace/{workspace_id}/pipe/{pipe_id}|Error Rate:> {pipe_error_rate_current:.2f}%
      (Total Requests: {pipe_total_requests_current}, Total Errors: {pipe_total_errors_current})
      {pipe_error_rate_change_percentage:+0.0}% error rate, {pipe_errors_change_percentage:+0.0}% errors.
              *   (If `pipe_stats_rt` was used) Query API Error Rate: {pipe_query_api_error_rate_current:.2f}% (Requests:
      {pipe_query_api_requests_current}, Errors: {pipe_query_api_errors_current})
              *   (If `pipe_stats_rt` was used) Other Error Rate: {pipe_other_error_rate_current:.2f}% (Requests:
      {pipe_other_requests_current}, Errors: {pipe_other_errors_current})
              *   *Anomaly Detection:* If error rate or errors changed by > 20%, indicate: "Significant change detected."
      4.  *Workspace Performance Summary:* Brief summary in two or three sentences.
          *   *Workspace: {workspace_name}*
              *   Total Requests: {workspace_total_requests_current} (Errors: {workspace_total_errors_current}, Error Rate:
      {workspace_error_rate_current:.2f}%) {workspace_requests_change_percentage:+0.0}% requests,
      {workspace_errors_change_percentage:+0.0}% errors.
              *   *Anomaly Detection:* If requests or errors changed by > 20%, indicate: "Significant change detected."

      Actionable insights summary in two to three sentences. For example: "Focus investigations on pipes with high error
      rates or those showing significant anomalies in requests or errors. Consider optimizing high-traffic pipes to improve
      performance and reduce errors. Further exploration could involve deep-diving into specific error messages or request
      patterns for identified problematic pipes."

      Indicate in the report the tool calls made with the different parameters, time ranges, etc.
      Example:
      *Data for current period ({start_date_current} to {end_date_current}) collected using `execute_query` from
      `{datasource_current_period}`. Data for previous period ({start_date_previous} to {end_date_previous}) collected
      using `execute_query` from `{datasource_previous_period}`.*

      Format bytes in GB, TB, PB, etc.
      Format numbers in K, M, B, etc.

      Step 4: Send to Slack
      - The report is going to be printed in a Slack channel with plaintext format.
      - Wrap titles into * for bold text
      - Use this format <url|title (replies)> for links
      - Sort lists by their primary metric in descending order (e.g., Top 15 Pipes by Requests sorted by Total Requests
      descending). If secondary sorting is needed, it should be clearly defined.