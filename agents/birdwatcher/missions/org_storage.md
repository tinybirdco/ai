      Step 1: Collect data

      - `execute_query` select now() to get the current date.
      - To get storage data, use the `execute_query` tool with the following SQL queries. The agent should replace
      `{start_date_current}` and `{end_date_current}` with the actual start and end dates provided by the user in
      'YYYY-MM-DD HH:MM:SS' format.
        - Query for current period:
          ```sql
          SELECT
              toStartOfDay(s.timestamp) AS day,
              w.name AS workspace_name,
              s.datasource_name,
              max(s.bytes) AS bytes,
              max(s.rows) AS rows,
              max(s.bytes_quarantine) AS bytes_quarantine,
              max(s.rows_quarantine) AS rows_quarantine
          FROM
              organization.datasources_storage AS s
          JOIN
              organization.workspaces AS w ON s.workspace_id = w.workspace_id
          WHERE
              s.timestamp >= toDateTime('{start_date_current}') AND s.timestamp < toDateTime('{end_date_current}')
          GROUP BY
              day,
              workspace_name,
              datasource_name
          ORDER BY
              day ASC,
              workspace_name ASC,
              datasource_name ASC
          ```
        - Instruct the agent to auto-fix errors and retry with different parameters if data is empty.
        - Instruct to get data for different time ranges to create comparables (e.g., previous period, previous year). The
      time ranges (daily, weekly, monthly) will be determined by the user's input.
        - Do not limit ranks to 5 elements, limit to 10 or 15.
        - Indicate proper date formats: 'YYYY-MM-DD HH:MM:SS'.

      Step 2: Analyze the data
        - Instruct in the prompt to use the data collected in the previous step to analyze the data.
        - Create different rules depending on the selected domain.
        - The report MUST include ranks, counters, or other metrics.
        - The report MUST include comparables, such as WoW growth or similar (depending on the user time range).
        - You MUST add instruction to detect anomalies, like sudden spikes or drop-offs in bytes, rows, or quarantine.
        - Reports MUST include both aggregations (total bytes, rows, quarantine across all workspaces and datasources) and
      detailed information for different relevant topics (top datasources by storage, workspaces with highest quarantine).
        - Reports include links to relevant sources for the given domain.

      Step 3: Build report:
      The report needs to be structured. Add 3 to 4 main topics as a numbered list.

      Each topic MUST be drilled down to specific metrics that's explanatory. Use bulleted list with 2 to 4 elements.

      All ranks and lists need to be bulleted.

      Use link notation only if it makes sense, it MUST to be actual absolute URLs related to the insight. Do not use link
      notation if it's not an actual link

      1.  *Overall Storage Overview:* Brief summary of the total storage, rows, and quarantine data for the current period
      and comparison with the previous period.
          *   Total Bytes: <https://docs.tinybird.co/reference/datasources/datasources-storage.html|Total bytes stored> and
      its growth/reduction compared to the previous period. Format bytes in GB, TB, PB, etc.
          *   Total Rows: <https://docs.tinybird.co/reference/datasources/datasources-storage.html|Total rows stored> and
      its growth/reduction compared to the previous period.
          *   Total Quarantine Bytes: <https://docs.tinybird.co/reference/datasources/datasources-storage.html|Total bytes
      in quarantine> and its growth/reduction compared to the previous period. Format bytes in GB, TB, PB, etc.
          *   Total Quarantine Rows: <https://docs.tinybird.co/reference/datasources/datasources-storage.html|Total rows in
      quarantine> and its growth/reduction compared to the previous period.

      2.  *Top Workspaces by Storage:* Brief summary of workspaces consuming the most storage.
          *   Top 10 Workspaces by Bytes: List of workspaces and their total bytes, ordered descending. Format bytes in GB,
      TB, PB, etc.
          *   Top 10 Workspaces by Quarantine Bytes: List of workspaces and their total quarantine bytes, ordered
      descending. Format bytes in GB, TB, PB, etc.

      3.  *Top Datasources by Storage:* Brief summary of datasources consuming the most storage.
          *   Top 15 Datasources by Bytes: List of datasources and their total bytes, ordered descending. Format bytes in
      GB, TB, PB, etc.
          *   Top 15 Datasources by Quarantine Rows: List of datasources and their total quarantine rows, ordered
      descending.

      4.  *Anomaly Detection:* Brief summary of any detected anomalies in storage or quarantine data.
          *   Sudden spikes/drop-offs in bytes or rows for specific datasources/workspaces with details on the affected
      entities and magnitude of change.
          *   Unusual increases in quarantine bytes or rows, indicating potential data ingestion issues.

      Actionable insights summary in two to three sentences. Include corrective measures, experiments the user can run,
      suggest further explorations.

      Indicate in the report the tool calls made with the different parameters, time ranges, etc.

      Format bytes in GB, TB, PB, etc.

      Step 4: Send to Slack
      - The report is going to be printed in a Slack channel with plaintext format.
      - Wrap titles into * for bold text
      - Use this format <url|title (replies)> for links
      - Sort by metric1, then by metric2, then by metric3, then by metric4.