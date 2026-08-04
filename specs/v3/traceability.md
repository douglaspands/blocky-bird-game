# Matriz de rastreabilidade — v3

Uma linha por critério de aceitação de [`requirements.md`](requirements.md), ligando o
requisito à seção de [`design.md`](design.md) que o resolve, à task de
[`tasks.md`](tasks.md) que o implementa e ao(s) teste(s) que o comprovam.

O documento é vigiado por `tests/test_traceability.py`, que falha o build quando um critério
de aceitação não aparece aqui ou quando esta matriz referencia um teste inexistente (R32.2,
R32.3). É o que impede a matriz de envelhecer em silêncio.

> **Completa até a task 67.** Todo critério `R1.1`–`R34.5` de `requirements.md` tem uma linha.
> Para os critérios cuja task implementadora ainda está pendente nesta versão (tasks 65, 66,
> 68–73 — docstrings/site, o próprio teste da matriz, cobertura, README e fechamento com
> aparelho real), a coluna Testes fica em branco: citar um teste ali seria inventar uma
> referência que `tests/test_traceability.py` (task 68) rejeitaria. Critérios que só um
> aparelho Android real comprova, sem nenhum caminho automatizável no desktop, usam o
> marcador `manual`, seguindo o que `tasks.md` já separa em "Requer aparelho Android real".

| Critério | Design | Task | Testes |
|---|---|---|---|
| R1.1 | 5 | 3 | `test_bird.py::test_flap_sets_impulse_and_upward_angle`, `test_input.py::test_mouse_and_touch_at_the_same_physical_point_agree` |
| R1.2 | 5 | 3 | `test_bird.py::test_gravity_accumulates_each_frame` |
| R1.3 | 5 | 3 | `test_bird.py::test_flap_sets_impulse_and_upward_angle`, `test_bird.py::test_angle_interpolates_down_while_falling`, `test_bird.py::test_angle_never_exceeds_max_down` |
| R1.4 | 5 | 3 | `test_bird.py::test_top_of_screen_clamps_position_without_negative_velocity` |
| R2.1 | 6 | 4 | `test_pipes.py::test_spawns_new_pipe_at_fixed_spacing` |
| R2.2 | 6 | 4 | `test_pipes.py::test_gap_is_within_safe_margins`, `test_pipes.py::test_new_pipe_freezes_current_gap_size_and_textures` |
| R2.3 | 6 | 4 | `test_pipes.py::test_update_moves_pipes_left_by_speed` |
| R2.4 | 6 | 4 | `test_pipes.py::test_pipe_removed_once_fully_off_screen` |
| R2.5 | 6, 34 | 4, 54 | `test_pipes.py::test_the_strips_draw_exactly_what_the_v2_loop_drew`, `test_pipes.py::test_a_pipe_of_another_biome_gets_its_own_pair_of_strips` |
| R3.1 | 6, 16 | 5 | `test_game.py::test_collision_with_ground_ends_round` |
| R3.2 | 9 | 10 | `test_game.py::test_collision_with_ground_ends_round` |
| R3.3 | 3, 12 | 6 | `test_ui_layout.py::test_game_over_screen_texts_do_not_overlap` |
| R3.4 | 3 | 6 | `test_game.py::test_flap_in_game_over_resets_to_pronto` |
| R3.5 | 6, 16 | 5, 14 | `test_bird.py::test_hitbox_is_scaled_and_centered_on_sprite` |
| R4.1 | 8 | 7 | `test_game.py::test_score_increments_once_per_pipe` |
| R4.2 | 8, 12 | 7 | `test_ui_layout.py::test_hud_score_text_in_bounds` |
| R4.3 | 8, 36 | 22, 60 | `test_score.py::test_save_and_load_roundtrip`, `test_game.py::test_reaching_game_over_writes_the_record` |
| R4.4 | 8 | 7 | `test_score.py::test_missing_file_falls_back_to_zero`, `test_score.py::test_corrupted_json_falls_back_to_zero`, `test_score.py::test_missing_key_falls_back_to_zero`, `test_score.py::test_wrong_type_falls_back_to_zero` |
| R4.5 | 23 | 22, 33 | `test_storage.py::test_save_dir_desktop_is_project_root`, `test_storage.py::test_save_dir_frozen_desktop_uses_executable_dir`, `test_storage.py::test_save_dir_android_uses_app_storage_path` |
| R5.1 | 7 | 8 | `test_biome.py::test_starts_on_overworld`, `test_biome.py::test_threshold_10_activates_cave`, `test_biome.py::test_threshold_25_activates_nether` |
| R5.2 | 7 | 8 | `test_pipes.py::test_new_pipe_uses_new_biome_params` |
| R5.3 | 7 | 12 | `test_pipes.py::test_new_pipe_freezes_current_gap_size_and_textures` |
| R5.4 | 7 | 8 | `test_biome.py::test_the_biome_fade_uses_image_alpha` |
| R6.1 | 3, 12 | 6 | `test_game.py::test_starts_in_pronto_state`, `test_ui_layout.py::test_ready_screen_texts_do_not_overlap` |
| R6.2 | 3 | 6 | `test_game.py::test_flap_in_pronto_transitions_to_jogando` |
| R6.3 | 3, 12 | 6 | `test_game.py::test_pause_toggle_freezes_physics`, `test_ui_layout.py::test_paused_overlay_texts_do_not_overlap` |
| R6.4 | 3 | 6 | `test_game.py::test_bare_tv_remote_reaches_every_state` |
| R7.1 | 10 | 2 | `test_render.py::test_every_generated_texture_is_converted` |
| R7.2 | 5, 10 | 2, 3 | `test_render.py::test_the_bee_texture_survives_the_conversion_with_its_transparency`, `test_bird_sprites.py::test_precompute_builds_every_combination_once` |
| R7.3 | 16, 34 | 5, 53 | `test_ground.py::test_the_ground_covers_the_canvas_from_edge_to_edge`, `test_ground.py::test_a_ground_frame_is_a_single_draw_call` |
| R7.4 | 17, 34 | 9, 55 | `test_decor.py::test_a_parallax_frame_takes_at_most_four_draw_calls`, `test_decor.py::test_the_strip_draws_exactly_what_the_v2_loop_drew` |
| R7.5 | 12, 19 | 6, 20 | `test_ui_layout.py::test_ready_screen_texts_do_not_overlap` |
| R7.6 | 19 | 20 | `test_render.py::test_the_font_cache_is_filled_with_converted_surfaces`, `test_perf.py::test_lines_usa_apenas_glifos_existentes` |
| R8.1 | 11 | 11 | |
| R8.2 | 11 | 11 | |
| R8.3 | 11, 12 | 11 | `test_game.py::test_tap_on_mute_icon_toggles_mute_without_side_effects` |
| R8.4 | 11, 14 | 11 | `test_sounds.py::test_audio_that_cannot_be_opened_leaves_the_game_playable` |
| R9.1 | 20 | 41 | `test_game.py::test_renderer_uses_the_computed_canvas`, `test_scale.py::test_matching_aspect_gives_scale_one_no_offset` |
| R9.2 | 2.1 | 26 | |
| R9.3 | 2.1 | 1 | |
| R9.4 | 13, 37 | 1, 63 | `test_game.py::test_sixty_fps_reproduces_the_v2_frame_loop_exactly` |
| R9.5 | 30 | 30 | manual |
| R10.1 | 13 | 11b | manual |
| R10.2 | 13 | 11b | manual |
| R10.3 | 13 | 11b | manual |
| R10.4 | 13 | 11b | manual |
| R10.5 | 13 | 11b | manual |
| R11.1 | 12 | 16 | `test_ui_layout.py::test_ready_screen_texts_do_not_overlap` |
| R11.2 | 12 | 16 | |
| R12.1 | 12 | 17 | `test_ui_layout.py::test_ready_screen_texts_do_not_overlap` |
| R12.2 | 12 | 17 | `test_score.py::test_missing_file_falls_back_to_zero` |
| R13.1 | 18 | 18 | manual |
| R13.2 | 18 | 19 | manual |
| R13.3 | 18, 24.3 | 29 | manual |
| R14.1 | 24.2 | 27 | `test_packaging.py::test_the_android_api_range_is_the_one_the_project_promises` |
| R14.2 | 24.2, 40 | 27, 62 | `test_packaging.py::test_every_real_device_still_has_an_architecture` |
| R14.3 | 20, 32 | 41, 45 | `test_viewport.py::test_canvas_keeps_the_real_aspect_ratio`, `test_viewport.py::test_play_area_is_always_the_same_world_column` |
| R14.4 | 24.2, 32.7, 40 | 27, 41, 48, 62 | `test_packaging.py::test_the_orientation_stays_locked_in_portrait`, `test_resize.py::test_portrait_orientation_hint_is_set` |
| R14.5 | 19 | 20 | `test_render.py::test_the_font_cache_is_filled_with_converted_surfaces` |
| R14.6 | 11, 14 | 30 | `test_sounds.py::test_audio_that_cannot_be_opened_leaves_the_game_playable` |
| R15.1 | 32.8 | 51 | `test_input.py::test_tap_on_a_decorative_band_flaps`, `test_input.py::test_finger_tap_in_game_area_flaps` |
| R15.2 | 21.2 | 23 | `test_game.py::test_back_in_jogando_pauses_without_quitting` |
| R15.3 | 21.2 | 23 | `test_game.py::test_back_in_pronto_quits`, `test_game.py::test_back_in_pausado_quits`, `test_game.py::test_back_in_game_over_quits` |
| R15.4 | 21.1, 21.3 | 23, 25 | `test_input.py::test_finger_tap_on_mute_icon_mutes_not_flaps`, `test_input.py::test_mouse_click_on_mute_icon_mutes_not_flaps`, `test_game.py::test_dpad_left_right_toggle_mute_only_when_pausado` |
| R15.5 | 21.3, 13 | 25 | `test_game.py::test_bare_tv_remote_reaches_every_state`, `test_input.py::test_mouse_and_touch_at_the_same_physical_point_agree` |
| R16.1 | 22 | 24 | `test_game.py::test_focus_lost_pauses_during_jogando`, `test_game.py::test_app_background_events_also_pause` |
| R16.2 | 22 | 24 | `test_game.py::test_focus_lost_does_not_auto_resume` |
| R16.3 | 23 | 22 | `test_storage.py::test_save_dir_android_uses_app_storage_path` |
| R16.4 | 36 | 60 | `test_game.py::test_going_to_the_background_writes_a_pending_record`, `test_game.py::test_going_to_the_background_while_paused_still_writes` |
| R17.1 | 24.1, 24.2 | 27, 28 | `test_packaging.py::test_the_spec_is_well_formed_ini_with_the_sections_buildozer_expects` |
| R17.2 | 24.3 | 29 | manual |
| R17.3 | 24.2 | 27 | `test_packaging.py::test_the_orientation_stays_locked_in_portrait` |
| R18.1 | 26 | 31 | |
| R18.2 | 26 | 31 | |
| R18.3 | 26 | 31 | |
| R18.4 | 26 | 31 | |
| R18.5 | 26 | 31 | |
| R18.6 | 26 | 31 | |
| R19.1 | 27 | 32 | `test_ui_layout.py::test_ready_screen_texts_do_not_overlap`, `test_ui_layout.py::test_paused_overlay_texts_do_not_overlap`, `test_ui_layout.py::test_game_over_screen_texts_do_not_overlap`, `test_ui_layout.py::test_hud_score_text_in_bounds` |
| R19.2 | 27 | 32 | `test_ui_layout.py::test_ready_screen_texts_do_not_overlap`, `test_ui_layout.py::test_hud_score_text_in_bounds` |
| R19.3 | 27 | 32 | `test_ui_layout.py::test_game_over_screen_texts_do_not_overlap` |
| R19.4 | 27 | 32 | `test_ui_layout.py::test_paused_overlay_texts_do_not_overlap` |
| R19.5 | 27 | 32 | `test_ui_layout.py::test_ready_screen_texts_do_not_overlap`, `test_ui_layout.py::test_paused_overlay_texts_do_not_overlap`, `test_ui_layout.py::test_game_over_screen_texts_do_not_overlap` |
| R20.1 | 28 | 34 | |
| R20.2 | 28 | 34 | |
| R20.3 | 28 | 34 | |
| R20.4 | 28 | 34 | |
| R20.5 | 28 | 34 | |
| R20.6 | 28 | 34 | |
| R20.7 | 28 | 34 | |
| R21.1 | 29.1 | 36 | `test_generate_app_icon.py::test_foreground_bee_fits_within_safe_zone`, `test_generate_app_icon.py::test_composed_icon_has_requested_size` |
| R21.2 | 29.3 | 36 | `test_assets.py::test_asset_path_source_run_resolves_project_root`, `test_assets.py::test_asset_path_frozen_resolves_meipass` |
| R21.3 | 29.3 | 36 | manual |
| R21.4 | 29.4 | 37 | `test_generate_app_icon.py::test_foreground_bee_fits_within_safe_zone`, `test_generate_app_icon.py::test_background_layer_has_no_alpha_channel` |
| R21.5 | 29.1, 29.4 | 37 | `test_generate_app_icon.py::test_foreground_bee_fits_within_safe_zone` |
| R21.6 | 29.1, 29.4 | 37 | `test_generate_app_icon.py::test_composed_icon_has_requested_size` |
| R21.7 | 29.1, 29.2 | 36 | `test_generate_app_icon.py::test_build_ico_contains_all_sizes_and_round_trips` |
| R22.1 | 31 | 42 | `test_packaging.py::test_the_app_is_named_blocky_bee` |
| R22.2 | 31 | 42 | `test_packaging.py::test_the_app_is_named_blocky_bee` |
| R22.3 | 31 | 42 | `test_score.py::test_missing_file_falls_back_to_zero` |
| R22.4 | 31 | 42 | manual |
| R23.1 | 32.2, 32.3 | 45 | `test_viewport.py::test_bands_tile_the_canvas_without_losing_a_pixel` |
| R23.2 | 32.2 | 45 | `test_viewport.py::test_play_area_is_always_the_same_world_column` |
| R23.3 | 32.7 | 45 | `test_game.py::test_android_display_is_fullscreen_at_native_resolution` |
| R23.4 | 32.3, 32.4 | 45, 46 | `test_viewport.py::test_canvas_matches_the_design_table`, `test_viewport.py::test_canvas_keeps_the_real_aspect_ratio` |
| R23.5 | 32.7, 40 | 48 | `test_resize.py::test_portrait_orientation_hint_is_set`, `test_packaging.py::test_the_orientation_stays_locked_in_portrait` |
| R23.6 | 32.7 | 48 | `test_resize.py::test_resize_recomputes_the_canvas_and_keeps_the_play_area` |
| R23.7 | 32.7 | 45 | `test_viewport.py::test_desktop_screen_size_is_wider_than_the_play_area` |
| R24.1 | 32.2, 32.4 | 45, 46 | `test_viewport.py::test_play_area_is_always_the_same_world_column` |
| R24.2 | 32.2 | 45, 46 | `test_bands.py::test_fall_is_identical_in_both_canvases` |
| R24.3 | 32.4 | 47 | `test_bands.py::test_pipe_spawns_at_the_play_right_edge`, `test_bands.py::test_time_from_spawn_to_bird_is_the_same_in_both_canvases` |
| R24.4 | 32.5 | 47 | `test_bands.py::test_side_bands_hide_a_pipe_that_has_not_entered_the_play_area`, `test_bands.py::test_the_pipe_under_the_band_is_drawn_before_it` |
| R24.5 | 32.4 | 46 | `test_bands.py::test_bird_ceiling_is_the_play_top_not_the_canvas_top`, `test_bands.py::test_ground_line_sits_on_the_play_bottom_not_the_canvas_bottom` |
| R25.1 | 32.3, 32.5 | 46 | `test_bands.py::test_the_phone_canvas_really_has_both_bands`, `test_bands.py::test_ground_fills_the_decorative_band_below_the_play_area` |
| R25.2 | 32.5 | 47 | `test_bands.py::test_side_band_is_opaque_over_its_whole_height`, `test_bands.py::test_band_ground_line_matches_the_play_ground_line` |
| R25.3 | 35 | 57 | `test_mobs.py::test_each_biome_has_three_varieties_and_none_repeats_across_biomes`, `test_mobs.py::test_every_field_carries_the_three_varieties_of_its_biome` |
| R25.4 | 35 | 57 | `test_mobs.py::test_the_whole_simulation_is_identical_with_and_without_mobs`, `test_mobs.py::test_a_mob_over_the_bird_does_not_collide`, `test_mobs.py::test_mobs_module_imports_nothing_from_the_game` |
| R25.5 | 32.6 | 47 | `test_bands.py::test_sky_parallax_and_ground_span_the_whole_canvas_width` |
| R25.6 | 32.8 | 46, 51 | `test_input.py::test_tap_on_a_decorative_band_flaps`, `test_input.py::test_tap_on_the_mute_icon_inside_the_sky_band_still_mutes` |
| R25.7 | 32.5 | 46 | `test_bands.py::test_hud_score_moves_into_the_sky_band`, `test_bands.py::test_mute_icon_sits_in_the_sky_band_when_it_fits` |
| R26.1 | 33.2, 33.3 | 49 | `test_render.py::test_first_level_is_the_accelerated_renderer` |
| R26.2 | 33.3 | 49 | `test_render.py::test_cascade_falls_to_the_sdl_chosen_renderer` |
| R26.3 | 33.3, 33.4 | 49 | `test_render.py::test_cascade_falls_to_the_surface_path`, `test_render.py::test_cascade_never_raises_to_the_caller` |
| R26.4 | 33.1, 33.5 | 49, 50 | `test_render.py::test_both_backends_draw_the_same_frame` |
| R26.5 | 33.3, 39 | 49, 50, 43 | `test_render.py::test_every_fallback_is_logged`, `test_perf.py::test_draw_overlay_mostra_o_backend_de_render`, `test_perf.py::test_game_informa_o_backend_ao_profiler` |
| R26.6 | 33.2 | 49 | `test_render.py::test_accelerated_renderer_is_asked_for_vsync` |
| R26.7 | 33.2, 40 | 49, 61 | `test_render.py::test_nearest_neighbour_scaling_is_requested` |
| R27.1 | 30 | 72 | manual |
| R27.2 | 34 | 53, 54, 55, 56 | `test_ground.py::test_a_ground_frame_is_a_single_draw_call`, `test_pipes.py::test_a_pipe_is_two_draw_calls`, `test_decor.py::test_a_parallax_frame_takes_at_most_four_draw_calls`, `test_bird_sprites.py::test_a_bird_frame_is_a_single_draw_call` |
| R27.3 | 36 | 58, 59, 55 | `test_alloc.py::test_a_playing_frame_stays_within_the_rect_budget`, `test_decor.py::test_no_random_generator_is_created_while_drawing`, `test_alloc.py::test_the_pipe_list_is_never_rebuilt` |
| R27.4 | 34 | 52 | `test_render.py::test_opaque_surface_is_converted_to_the_display_format`, `test_render.py::test_every_generated_texture_is_converted` |
| R27.5 | 36 | 60 | `test_game.py::test_beating_the_record_while_playing_does_not_touch_the_disk`, `test_game.py::test_no_disk_write_happens_during_a_whole_played_round`, `test_game.py::test_reaching_game_over_writes_the_record` |
| R27.6 | 40 | 61 | `test_input.py::test_the_continuous_motion_events_are_blocked`, `test_input.py::test_a_blocked_event_never_becomes_a_python_object` |
| R27.7 | 34 | 54 | `test_pipes.py::test_the_pipe_born_at_the_play_edge_is_not_drawn_on_a_2_3_canvas`, `test_pipes.py::test_visibility_is_decided_by_the_canvas_edges` |
| R28.1 | 37 | 63 | `test_game.py::test_a_sixty_fps_frame_advances_exactly_one_step` |
| R28.2 | 37 | 63 | `test_game.py::test_a_thirty_fps_frame_advances_two_steps`, `test_game.py::test_the_number_of_steps_per_frame_has_a_ceiling` |
| R28.3 | 37 | 63 | `test_game.py::test_a_long_stall_is_clamped_instead_of_becoming_a_leap`, `test_game.py::test_the_two_defences_are_consistent_and_the_inner_one_binds_first` |
| R28.4 | 37 | 63 | `test_game.py::test_sixty_fps_reproduces_the_v2_frame_loop_exactly` |
| R29.1 | 38 | 64 | `test_quality.py::test_frames_outside_playing_are_not_measured`, `test_quality.py::test_the_level_is_measured_and_dropped_while_playing` |
| R29.2 | 38 | 64 | `test_quality.py::test_sustained_low_frame_rate_drops_a_level`, `test_quality.py::test_each_level_turns_off_more_decoration_than_the_one_above` |
| R29.3 | 38 | 64 | `test_quality.py::test_the_rules_are_identical_at_every_quality_level` |
| R29.4 | 38 | 64 | `test_quality.py::test_the_rise_needs_a_longer_window_than_the_drop`, `test_quality.py::test_a_device_on_the_edge_settles_instead_of_bouncing` |
| R29.5 | 38 | 64 | `test_quality.py::test_the_level_survives_between_sessions`, `test_quality.py::test_the_file_is_written_next_to_the_highscore` |
| R29.6 | 38 | 64 | `test_quality.py::test_a_missing_file_means_full_quality`, `test_quality.py::test_a_corrupted_file_means_full_quality` |
| R30.1 | 39 | 43 | `test_perf.py::test_draw_overlay_mostra_o_backend_de_render`, `test_perf.py::test_end_update_e_end_draw_medem_intervalos_separados` |
| R30.2 | 39 | 43 | `test_perf.py::test_enabled_desligado_por_padrao`, `test_perf.py::test_game_sem_profiler_por_padrao` |
| R30.3 | 39 | 44 | `test_benchmark.py::test_result_formata_linha_de_tabela_markdown` |
| R30.4 | 39 | 44 | `test_benchmark.py::test_percentile_p95_pega_a_cauda`, `test_benchmark.py::test_result_formata_linha_de_tabela_markdown` |
| R30.5 | 30 | 73 | |
| R31.1 | 41 | 65 | |
| R31.2 | 41 | 65 | |
| R31.3 | 41 | 65 | |
| R31.4 | 41 | 66 | |
| R31.5 | 41 | 66 | |
| R32.1 | 42 | 67 | |
| R32.2 | 42 | 68 | |
| R32.3 | 42 | 68 | |
| R32.4 | 42 | 69 | |
| R33.1 | 43 | 71 | |
| R33.2 | 43 | 71 | |
| R33.3 | 43 | 71 | |
| R33.4 | 43 | 71 | |
| R33.5 | 43 | 71 | |
| R34.1 | 32.8 | 51 | `test_input.py::test_tap_on_a_decorative_band_flaps` |
| R34.2 | 32.8 | 51 | `test_input.py::test_mouse_and_touch_at_the_same_physical_point_agree` |
| R34.3 | 32.8 | 51 | `test_input.py::test_finger_tap_outside_the_canvas_is_ignored` |
| R34.4 | 32.8 | 51 | `test_input.py::test_tap_on_a_band_starts_and_restarts_the_match` |
| R34.5 | 32.8 | 51 | `test_mobs.py::test_the_whole_simulation_is_identical_with_and_without_mobs`, `test_input.py::test_tap_on_a_decorative_band_flaps` |
