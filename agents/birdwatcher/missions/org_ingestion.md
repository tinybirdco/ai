Step 1: Collect data

- `execute_query` select now() to get the current date.
- Define date ranges and previous period for growth calculations (YYYY-MM-DD).
- Auto-fix errors and retry queries with different parameters if data is empty.
- Change the queries to group by the proper granularity (e.g. day, week, month, etc.)

**Query 1: Ingested Bytes by Event Type**
- Get total ingested bytes per `event_type` the current and previous periods.
- Use the `organization.datasources_ops_log` datasource.
- Query:
```sql
SELECT
    toDate(timestamp) AS event_date,
    event_type,
    sum(written_bytes) AS total_ingested_bytes
FROM organization.datasources_ops_log
WHERE toDate(timestamp) between '{start_date}' and '{end_date}' AND event_type IS NOT NULL
GROUP BY
    event_date,
    event_type
ORDER BY
    total_ingested_bytes DESC
```
- Run this query twice: once with both periods.
- Ensure results are ordered by `total_ingested_bytes` in descending order.

**Query 2: Ingested Bytes by Workspace**
- Get total ingested bytes per `workspace` for both periods.
- Use the `organization.datasources_ops_log` datasource.
- Query:
```sql
SELECT
    toDate(timestamp) AS event_date,
    w.name as workspace,
    sum(written_bytes) AS total_ingested_bytes
FROM organization.datasources_ops_log
LEFT JOIN organization.workspaces w
USING workspace_id
WHERE toDate(timestamp) between '{start_date}' and '{end_date}' AND workspace IS NOT NULL
GROUP BY
    event_date,
    workspace
ORDER BY
    total_ingested_bytes DESC
```
- Run this query twice for both periods.
- Limit ranks to the top 10 workspaces.

**Query 3: Ingested Bytes by Workspace and Datasource**
- Get total ingested bytes per `workspace` and `datasource_name` for both periods.
- Use the `organization.datasources_ops_log` datasource.
- Query:
```sql
SELECT
    toDate(timestamp) AS event_date,
    w.name as workspace,
    datasource_name,
    sum(written_bytes) AS total_ingested_bytes
FROM organization.datasources_ops_log
LEFT JOIN organization.workspaces w
USING workspace_id
WHERE toDate(timestamp) between '{start_date}' and '{end_date}' AND workspace IS NOT NULL AND datasource_name IS NOT NULL
GROUP BY
    event_date,
    workspace,
    datasource_name
ORDER BY
    total_ingested_bytes DESC
```
- Run this query twice for both periods.
- Limit ranks to the top 15 workspace-datasources combinations.

Step 2: Analyze the data
- Use the data collected in the previous step to analyze the daily ingestion.
- Calculate the total ingested bytes for both periods.
- For each `event_type`, calculate the total ingested bytes for both periods, and compute the
Day-over-Day (DoD) growth.
- For each `workspace`, calculate the total ingested bytes for both periods, and compute the DoD
growth. Identify the top 10 workspaces by ingested bytes for current period.
- For each `workspace` and `datasource_name` combination, calculate the total ingested bytes for both periods, and compute the DoD growth. Identify the top 15 workspace-datasources by ingested bytes for current period.
- Detect anomalies: identify any sudden spikes or drop-offs (e.g., > 20% DoD change) in total ingested bytes, by
event type, by workspace, and by workspace-datasource.

Step 3: Build report:
The report needs to be structured into the following topics:

1.  *Daily Ingestion Summary:* A brief summary of the total ingested bytes for the report date and its Day-over-Day
growth.
    *   Total ingested bytes for {today} and Day-over-Day growth.
    *   Summary of significant changes in total ingestion (spikes/drop-offs).
2.  *Ingestion Breakdown by Event Type:* An overview of ingestion categorized by event type.
    *   Top 5 event types by ingested bytes for {today} and their respective DoD growth.
    *   Any notable anomalies (spikes or drops) in specific event types, including the event type and its DoD change.
3.  *Ingestion Breakdown by Workspace:* A detailed look at ingestion across different workspaces.
    *   Top 10 workspaces by ingested bytes for {today} and their respective DoD growth.
    *   Identification of workspaces with significant changes (spikes or drops) in ingestion, including the workspace
ID and its DoD change.
4.  *Ingestion Breakdown by Workspace and Datasource:* Granular insights into ingestion at the datasource level
within each workspace.
    *   Top 15 workspace-datasource combinations by ingested bytes for {today} and their respective DoD growth.
    *   Highlight any specific workspace-datasource pairs showing unusual ingestion patterns (e.g., new high
ingestion, significant drops).

Actionable insights summary in two to three sentences. Include corrective measures, experiments the user can run,
suggest further explorations. For instance, "Investigate the sudden drop in ingestion for workspace X. Check the data
source and its upstream systems."

Indicate in the report the tool calls made with the different parameters, time ranges, etc.
Format bytes in GB, TB, PB, etc.

Step 4: Send to Slack
- The report is going to be printed in a Slack channel with plaintext format.
- Wrap titles into * for bold text
- Use this format <url|title (replies)> for links (if applicable, e.g., link to Tinybird UI for specific data source,
but for this report, it's unlikely).
- Sort all ranks by ingested bytes in descending order.