 Step 1: Collect data

      - `execute_query` select now() to get the current date.
      - For each time range (current period and previous period for comparison), collect data using the following
      endpoints. Instruct the agent to auto-fix errors, retry with different parameters if data is empty. Ensure dates are
      in 'YYYY-MM-DD' format.
        - `get_incidents_by_week`: To get weekly incident counts. Parameters: `start_date`, `end_date`. Use `q='SELECT
      week_start_date, incidents_count FROM _'`
        - `get_incidents_by_severity`: To get incident counts grouped by severity. Parameters: `start_date`, `end_date`,
      `status` (default to 'closed' for primary analysis, but also get 'all' for a broader view if needed). Use `q='SELECT
      severity, incidents_count FROM _ ORDER BY incidents_count DESC LIMIT 15'`
        - `get_incidents_by_status`: To get incident counts grouped by status. Parameters: `start_date`, `end_date`. Use
      `q='SELECT status, incidents_count FROM _ ORDER BY incidents_count DESC'`
        - `get_incident_aps_by_priority`: To get incident action points aggregated by priority. Parameters: `start_date`,
      `end_date`, `status`. Use `q='SELECT priority, ap_count FROM _ ORDER BY ap_count DESC LIMIT 15'`
        - `get_incident_aps_by_team`: To get incident action points aggregated by team. Parameters: `start_date`,
      `end_date`, `status`. Use `q='SELECT team, ap_count FROM _ ORDER BY ap_count DESC LIMIT 15'`
        - `get_incidents_table`: To get detailed information for the most recent incidents. Parameters: `start_date`,
      `end_date`. Use `q='SELECT incident_id, title, severity, status, created_at, acknowledged_at, resolved_at FROM _
      ORDER BY created_at DESC LIMIT 10'`

      Step 2: Analyze the data
        - Use the data collected in the previous step to analyze trends, distributions, and anomalies.
        - Calculate total incident counts for the current and previous periods to determine Week-over-Week (WoW) or
      Month-over-Month (MoM) growth/decline.
        - Identify the top 10-15 incident severities and action point priorities/teams.
        - Analyze the distribution of incidents by status (open, closed, resolved).
        - Detect anomalies by comparing incident counts and key metrics between the current and previous periods. Look for
      significant spikes or drop-offs in any category.
        - Summarize key incidents from the `get_incidents_table` for detailed review.

      Step 3: Build report:
      The report needs to be structured. Add 4 main topics as a numbered list.

      Each topic MUST be drilled down to specific metrics that's explanatory. Use bulleted list with 2 to 4 elements.

      All ranks and lists need to be bulleted.

      Use link notation only if it makes sense, it MUST to be actual absolute URLs related to the insight. Do not use link
      notation if it's not an actual link

      1.  *Overall Incident Summary:* A brief summary of the incident activity for the period, including total counts and
      comparison to the previous period.
          *   Total incidents for the current period: [Number] (WoW/MoM change: [Percentage]%)
          *   Trend of incidents by week: [Description of trend, e.g., stable, increasing, decreasing]
          *   Average time to resolve incidents: [Duration] (if calculable from `get_incidents_table`)
      2.  *Incident Severity and Status Breakdown:* Detailed analysis of incidents by their severity and current status.
          *   Top 5 incident severities:
              *   [Severity 1]: [Count] incidents
              *   [Severity 2]: [Count] incidents
              *   [Severity 3]: [Count] incidents
              *   [Severity 4]: [Count] incidents
              *   [Severity 5]: [Count] incidents
          *   Incident status distribution: [Percentage]% Closed, [Percentage]% Open, [Percentage]% Resolved
      3.  *Action Points Analysis:* Insights into the distribution of incident action points by priority and responsible
      team.
          *   Top 5 action point priorities:
              *   [Priority 1]: [Count] action points
              *   [Priority 2]: [Count] action points
              *   [Priority 3]: [Count] action points
              *   [Priority 4]: [Count] action points
              *   [Priority 5]: [Count] action points
          *   Top 5 teams with the most action points:
              *   [Team 1]: [Count] action points
              *   [Team 2]: [Count] action points
              *   [Team 3]: [Count] action points
              *   [Team 4]: [Count] action points
              *   [Team 5]: [Count] action points
      4.  *Key Incidents and Anomalies:* Highlights of specific incidents requiring attention or significant deviations
      from the norm.
          *   Notable incidents this period:
              *   [Incident ID]: [Title] (Severity: [Severity], Status: [Status])
              *   [Incident ID]: [Title] (Severity: [Severity], Status: [Status])
              *   [Incident ID]: [Title] (Severity: [Severity], Status: [Status])
          *   Detected anomalies: [Describe any significant spikes or drop-offs in incident metrics, e.g., "A sudden 50%
      increase in critical incidents observed on YYYY-MM-DD."]

      Actionable insights summary in two to three sentences. Include corrective measures, experiments the user can run,
      suggest further explorations.
      Example: "The increase in critical incidents suggests a need for deeper investigation into recent changes or
      deployments. Consider reviewing incident post-mortems for recurring patterns and implementing targeted preventative
      measures. Further exploration could involve analyzing the root causes of the top 3 severities."

      Indicate in the report the tool calls made with the different parameters, time ranges, etc.
      Example:
      `default_api.get_incidents_by_week(start_date='YYYY-MM-DD', end_date='YYYY-MM-DD', q='SELECT week_start_date,
      incidents_count FROM _')`

      Step 4: Send to Slack
      - The report is going to be printed in a Slack channel with plaintext format.
      - Wrap titles into * for bold text
      - Use this format <url|title (replies)> for links
      - Sort by metric1, then by metric2, then by metric3, then by metric4.