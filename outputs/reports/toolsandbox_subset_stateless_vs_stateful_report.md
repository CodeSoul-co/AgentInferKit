# Stateless vs Stateful Comparison Report

## Overview
- Total cases: 40
- Stateful passed cases: 40
- Stateless passed cases: 40
- Stateful all-calls-succeeded count: 36
- Stateless all-calls-succeeded count: 40

## Overview Metrics
- Stateful success rate: 96.83%
- Stateless success rate: 100.00%
- Stateful invalid call rate: 0.00%
- Stateless invalid call rate: 0.00%
- Stateful recovery rate: 100.00%
- Stateless recovery rate: 0.00%
- Stateful average steps: 3.15
- Stateless average steps: 1.50
- Stateful final state correctness: 100.00%
- Stateless final state correctness: 100.00%
- Cases with step count difference: 38
- Cases with explicit dependency resolution: 0
- Cases with query before index: 0
- Cases with overwrite without re-index: 0
- Cases with trajectory divergence: 38
- Cases with snapshot semantics difference: 0
- Cases with retrieval outcome difference: 0

## Overall Conclusion
Across the evaluated cases, the stateful setting introduced explicit dependency-management steps that were absent or less prominent in the stateless baseline. The two settings also exhibited stable trajectory-level divergence, indicating that the stateful formulation changes the tool-use process rather than only the final outcome.

## toolsandbox::add_contact_with_name_and_phone_number

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 2
- Stateful sequence: add_contact -> end_conversation
- Stateless sequence: add_contact -> end_conversation
- Key difference: This ToolSandbox case is already a direct final-state mutation, so stateful and stateless trajectories remain structurally similar.
- Key process difference: Stateful and stateless trajectories were structurally similar in this case.

## toolsandbox::modify_contact_with_message_recency_alt

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 5 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 5
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Stateless sequence: modify_contact -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::remove_contact_by_phone_ambiguous_alt

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 1
- Stateful sequence: search_contacts -> remove_contact -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::modify_contact_with_message_recency_multiple_user_turn_alt

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 5 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 5
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Stateless sequence: modify_contact -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::remove_contact_by_phone_multiple_user_turn

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 1
- Stateful sequence: search_contacts -> remove_contact -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::update_contact_relationship_with_relationship

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 4 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 3 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 4
- Stateless steps: 3
- Stateful sequence: search_contacts -> modify_contact -> modify_contact -> end_conversation
- Stateless sequence: modify_contact -> modify_contact -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::remove_contact_by_phone_ambiguous

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 1
- Stateful sequence: search_contacts -> remove_contact -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::remove_contact_with_id

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: remove_contact -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_contact_with_name_and_phone_number_10_distraction_tools

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 2
- Stateful sequence: add_contact -> end_conversation
- Stateless sequence: add_contact -> end_conversation
- Key difference: This ToolSandbox case is already a direct final-state mutation, so stateful and stateless trajectories remain structurally similar.
- Key process difference: Stateful and stateless trajectories were structurally similar in this case.

## toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: datetime_info_to_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 5 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 3 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 5
- Stateless steps: 3
- Stateful sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Stateless sequence: set_low_battery_mode_status -> set_wifi_status -> add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_week_delta_and_time_and_location_multiple_user_turn_alt

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 1
- Stateful sequence: search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_date_and_time_alt_all_tools

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: datetime_info_to_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_weekday_delta_and_time_alt_10_distraction_tools

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_days_till_holiday

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 6 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 6
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_days_till_holiday_alt

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 6 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 6
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_address_with_lat_lon

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: search_lat_lon -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_stock_symbol_with_company_name

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: search_stock -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_temperature

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: search_weather_around_lat_lon -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_days_till_holiday_multiple_user_turn

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 6 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 6
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_days_till_holiday_3_distraction_tools

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 6 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 6
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::find_days_till_holiday_3_distraction_tools_arg_description_scrambled

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 6 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 6
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_message_with_recency_latest_multiple_user_turn

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 2
- Stateful sequence: search_messages -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_message_with_recency_latest_multiple_user_turn_alt

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 2
- Stateful sequence: search_messages -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_message_with_recency_latest_alt

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 2
- Stateful sequence: search_messages -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_message_with_recency_latest

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 2
- Stateful sequence: search_messages -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_message_with_recency_oldest

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 4 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 4
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_message_with_recency_oldest_alt

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 4 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 4
- Stateless steps: 2
- Stateful sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_sender_phone_number_with_content

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: search_messages -> end_conversation
- Stateless sequence: end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::search_message_with_recency_latest_multiple_user_turn_3_distraction_tools

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 2
- Stateful sequence: search_messages -> end_conversation -> end_conversation
- Stateless sequence: end_conversation -> end_conversation
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: datetime_info_to_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_date_and_time_alt

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: datetime_info_to_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_weekday_delta_and_time_alt

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::add_reminder_content_and_week_delta_and_time_alt

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 1
- Stateful sequence: get_current_timestamp -> add_reminder
- Stateless sequence: add_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::modify_reminder_with_recency_latest

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 1
- Stateful sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Stateless sequence: modify_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.

## toolsandbox::modify_reminder_with_recency_latest_alt

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory.
- Stateful outcome: Stateful completed 3 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 1 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 1
- Stateful sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Stateless sequence: modify_reminder
- Key difference: Stateful ToolSandbox execution preserved helper/search/tool-trace milestones, while the stateless baseline collapsed the task to final-state mutations and final user-visible output.
- Key process difference: Stateful trajectory required an extra dependency-resolution step.
