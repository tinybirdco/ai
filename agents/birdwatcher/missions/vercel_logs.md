Step 1: Collect data

      - `execute_query` select now() to get the current date.
      - For each time range (e.g., current week, previous week):
          - Retrieve overall usage and error trends using `log_timeseries`.
              - Endpoint: `log_timeseries`
              - Parameters:
                  - `start_date`: Use format `YYYY-MM-DD HH:MM:SS` (e.g., '2024-01-01 00:00:00').
                  - `end_date`: Use format `YYYY-MM-DD HH:MM:SS` (e.g., '2024-01-07 23:59:59').
                  - `q`: `SELECT date, total_requests, error_count FROM _`
              - Instruct the agent to auto-fix errors and retry if no data is returned.
          - Retrieve detailed log analysis for errors using `log_analysis`.
              - Endpoint: `log_analysis`
              - Parameters:
                  - `start_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `end_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `level`: `['error']`
                  - `page_size`: 100 (or higher if needed for comprehensive analysis)
                  - `q`: `SELECT timestamp, request_method, status_code, service, request_path, message, host FROM _`
              - Instruct the agent to auto-fix errors and retry if no data is returned.
          - Retrieve top requested paths and their status codes using `log_analysis`.
              - Endpoint: `log_analysis`
              - Parameters:
                  - `start_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `end_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `q`: `SELECT request_path, status_code, sum(total_requests) AS total_requests_for_path FROM _ GROUP BY
      request_path, status_code ORDER BY total_requests_for_path DESC LIMIT 15`
              - Instruct the agent to auto-fix errors and retry if no data is returned.
          - Retrieve top services by request count using `log_analysis`.
              - Endpoint: `log_analysis`
              - Parameters:
                  - `start_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `end_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `q`: `SELECT service, sum(total_requests) AS total_requests_for_service FROM _ GROUP BY service ORDER
      BY total_requests_for_service DESC LIMIT 10`
              - Instruct the agent to auto-fix errors and retry if no data is returned.
          - Retrieve top error messages using `log_analysis`.
              - Endpoint: `log_analysis`
              - Parameters:
                  - `start_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `end_date`: Use format `YYYY-MM-DD HH:MM:SS`.
                  - `level`: `['error']`
                  - `q`: `SELECT message, count() AS error_count FROM _ GROUP BY message ORDER BY error_count DESC LIMIT
      10`
              - Instruct the agent to auto-fix errors and retry if no data is returned.

      Step 2: Analyze the data
        - Calculate weekly growth (WoW) for total requests and error counts.
        - Identify periods with significant spikes or drop-offs in total requests or error counts (anomalies).
        - Summarize the most frequent error messages, status codes, and affected request paths/services.
        - Analyze the distribution of status codes for the most active paths.
        - Determine which services generate the most traffic and which have the highest error rates.

      Step 3: Build report:
      The report needs to be structured. Add 3 to 4 main topics as a numbered list.

      Each topic MUST be drilled down to specific metrics that's explanatory. Use bulleted list with 2 to 4 elements.

      All ranks and lists need to be bulleted.

      Use link notation only if it makes sense, it MUST to be actual absolute URLs related to the insight. Do not use link
      notation if it's not an actual link

      1.  *Overall Usage & Performance:* Summary of total requests and error counts for the period, along with WoW growth.
      Highlight any significant spikes or drops in traffic or errors.
          *   Total Requests: [Number] (WoW: [+/- %])
          *   Total Errors: [Number] (WoW: [+/- %])
          *   <link_to_log_timeseries_graph|Traffic & Error Trends Over Time>: Visual representation of requests and
      errors.
          *   Notable Anomalies: Identify and describe any unusual spikes or dips in traffic or errors, including specific
      timestamps if possible.
      2.  *Error Analysis:* Detailed breakdown of the most common errors and their impact.
          *   Top 5 Error Messages:
              *   "[Error Message 1]" (Count: [Number])
              *   "[Error Message 2]" (Count: [Number])
              *   ...
          *   Top 5 Error Status Codes:
              *   "[Status Code 1]" (Count: [Number])
              *   "[Status Code 2]" (Count: [Number])
              *   ...
          *   <link_to_log_analysis_error_filter|Detailed Error Logs>: Link to filtered log analysis for further
      investigation.
      3.  *Service & Path Performance:* Overview of service and request path performance, highlighting areas with high
      traffic or high error rates.
          *   Top 5 Request Paths by Volume:
              *   "[Path 1]" (Requests: [Number], Error Rate: [X%])
              *   "[Path 2]" (Requests: [Number], Error Rate: [Y%])
              *   ...
          *   Top 5 Services by Request Volume:
              *   "[Service 1]" (Requests: [Number], Errors: [Number])
              *   "[Service 2]" (Requests: [Number], Errors: [Number])
              *   ...
          *   <link_to_log_analysis_top_paths|Request Path Breakdown>: Link to detailed breakdown of top request paths and
      their status codes.
      4.  *Actionable Insights Summary:* Provide a concise summary of key findings and recommendations.
          *   Investigate the root cause of "[Most Frequent Error Message]" as it's contributing significantly to overall
      errors.
          *   Monitor the performance of "[Service/Path with High Error Rate]" for potential bottlenecks or issues.
          *   Consider implementing caching strategies for "[High Traffic Path]" to reduce load and improve response times,
      if not already in place.

      Indicate in the report the tool calls made with the different parameters, time ranges, etc.

      Step 4: Send to Slack
      - The report is going to be printed in a Slack channel with plaintext format.
      - Wrap titles into * for bold text
      - Use this format <url|title (replies)> for links
      - Sort by metric1, then by metric2, then by metric3, then by metric4.