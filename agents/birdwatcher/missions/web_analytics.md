Step 1: Collect data

      - `execute_query` select now() to get the current date.
      - Collect web analytics data using the following endpoints for two time ranges:
          - **Current Week Data**: `date_from` (7 days ago from today's date), `date_to` (today's date)
          - **Previous Week Data**: `date_from` (14 days ago from today's date), `date_to` (7 days ago from today's date)

          - **`kpis`**:
              - Parameters: `date_from`, `date_to`
              - Description: Summary with general KPIs including visits, page views, bounce rate, and average session
      duration.
          - **`top_pages`**:
              - Parameters: `date_from`, `date_to`, `limit=10`
              - Description: Most visited pages.
          - **`top_browsers`**:
              - Parameters: `date_from`, `date_to`, `limit=10`
              - Description: Top browsers by visits.
          - **`top_locations`**:
              - Parameters: `date_from`, `date_to`, `limit=10`
              - Description: Top visiting countries by visits.
          - **`top_devices`**:
              - Parameters: `date_from`, `date_to`, `limit=10`
              - Description: Top device types by visits.
          - **`top_sources`**:
              - Parameters: `date_from`, `date_to`, `limit=10`
              - Description: Top traffic sources by visits.

      - Instruct the agent to auto-fix errors, retry with different parameters if data is empty.
      - Do not limit ranks to 5 elements, limit to 10 elements.
      - Use 'YYYY-MM-DD' date format for `date_from` and `date_to` parameters.

      Step 2: Analyze the data
        - Use the data collected in the previous step to analyze the web analytics data.
        - The report MUST include the following:
          - **Key Performance Indicators (KPIs)**: Total visits, total page views, bounce rate, and average session
      duration for both current and previous weeks.
          - **Week-over-Week (WoW) Growth**: Calculate the percentage change for all KPIs from the previous week to the
      current week.
          - **Top 10 Pages**: List the top 10 most visited pages for the current week and compare their performance
      (visits) with the previous week.
          - **Top 10 Browsers**: List the top 10 browsers for the current week and analyze changes in usage.
          - **Top 10 Locations**: List the top 10 countries for the current week and identify any significant shifts.
          - **Top 10 Devices**: List the top 10 device types for the current week and observe any trends.
          - **Top 10 Traffic Sources**: List the top 10 traffic sources for the current week and note any significant
      changes in referral traffic.
        - Add instruction to detect anomalies, such as sudden spikes or drop-offs in visits, page views, or bounce rate.
      Highlight any pages, browsers, locations, devices, or sources that show unusual activity.
        - Reports MUST include both aggregations (total visits, overall bounce rate) and detailed information (top pages,
      top sources).
        - Reports include links to relevant sources for the given domain. For example, for top pages, assume a base URL
      like `https://example.com/pages/` and concatenate the page path to create a clickable URL.

      Step 3: Build report:
      The report needs to be structured. Add 3 to 4 main topics as a numbered list.

      Each topic MUST be drilled down to specific metrics that's explanatory. Use bulleted list with 2 to 4 elements.

      All ranks and lists need to be bulleted.

      Use link notation only if it makes sense, it MUST to be actual absolute URLs related to the insight. Do not use link
      notation if it's not an actual link

      1.  *Overall Performance Overview:* A brief summary of the website's performance for the current week, highlighting
      major changes compared to the previous week.
          *   Total Visits: [current week visits] (WoW: [growth/decline]%)
          *   Total Page Views: [current week page views] (WoW: [growth/decline]%)
          *   Bounce Rate: [current week bounce rate]% (WoW: [growth/decline]%)
          *   Average Session Duration: [current week avg session duration] (WoW: [growth/decline]%)
      2.  *Content & User Engagement:* Insights into which content is performing well and how users are engaging with it.
          *   *Top 10 Pages:*
              - <url|https://example.com/[page_path]> [Page Name]: [visits] visits (WoW: [growth/decline]%) - [Summary of
      insight, e.g., anomaly detected or consistent growth]
              - ... (repeat for other top pages)
          *   *User Engagement Trends:* Highlight significant changes in bounce rate or session duration across different
      segments if available (e.g., by device type).
      3.  *Audience & Traffic Insights:* Understanding who the users are and where they are coming from.
          *   *Top 10 Locations:*
              - [Country Name]: [visits] visits (WoW: [growth/decline]%) - [Summary of insight]
              - ... (repeat for other top locations)
          *   *Top 10 Devices:*
              - [Device Type]: [visits] visits (WoW: [growth/decline]%) - [Summary of insight]
              - ... (repeat for other top devices)
          *   *Top 10 Traffic Sources:*
              - [Source Name]: [visits] visits (WoW: [growth/decline]%) - [Summary of insight, e.g., new significant
      referrer, drop in organic traffic]
              - ... (repeat for other top sources)
          *   *Top 10 Browsers:*
              - [Browser Name]: [visits] visits (WoW: [growth/decline]%) - [Summary of insight]
              - ... (repeat for other top browsers)
      4.  *Actionable Insights & Recommendations:* Based on the analysis, provide concrete, actionable recommendations.
          *   Brief summary of key takeaways and their implications.
          *   Suggest corrective measures, experiments (A/B tests, content updates), or further explorations (e.g., deep
      dive into specific traffic sources or user segments).

      Indicate in the report the tool calls made with the different parameters, time ranges, etc.

      Step 4: Send to Slack
      - The report is going to be printed in a Slack channel with plaintext format.
      - Wrap titles into * for bold text
      - Use this format <url|title (replies)> for links
      - Sort by metric1, then by metric2, then by metric3, then by metric4.