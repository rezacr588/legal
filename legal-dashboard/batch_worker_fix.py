def batch_generate_worker(target_count: int, model: str = None):
    """Background worker for batch generation"""
    global batch_generation_state

    with app.app_context():
        try:
            client = get_groq_client()

            if model is None:
                model = DEFAULT_MODEL

            # Load existing dataset
            df_existing = pl.read_parquet(PARQUET_PATH)
            current_count = len(df_existing)
            samples_needed = target_count - current_count

            # Check if target is already met
            if samples_needed <= 0:
                batch_generation_state.update({
                    'running': False,
                    'completed_at': datetime.now().isoformat(),
                    'total': 0,
                    'progress': 0,
                    'samples_generated': 0,
                    'errors': [{'error': f'Target already met: {current_count} samples exist, target is {target_count}'}]
                })
                save_batch_to_db(batch_generation_state)
                return

            batch_generation_state.update({
                'total': samples_needed,
                'progress': 0,
                'samples_generated': 0,
                'total_tokens': 0,
                'current_model': model,
                'errors': []
            })

            generated_samples = []
            minute_start = time.time()
            minute_requests = 0
            minute_tokens = 0

            # Apply filters if provided
            topic_filter = batch_generation_state.get('topic_filter')
            difficulty_filter = batch_generation_state.get('difficulty_filter')
            reasoning_instruction = batch_generation_state.get('reasoning_instruction')

            # Prepare topic cycle based on filters
            if topic_filter:
                # Find matching topic
                filtered_topics = [t for t in TOPICS if f"{t[0]} - {t[1]}" == topic_filter]
                if not filtered_topics:
                    filtered_topics = TOPICS  # Fallback to all topics
            else:
                filtered_topics = TOPICS

            topic_cycle = filtered_topics * (samples_needed // len(filtered_topics) + 1)

            for i in range(samples_needed):
                if not batch_generation_state['running']:
                    break

                practice_area, topic, original_difficulty = topic_cycle[i]

                # Apply difficulty filter if provided
                difficulty = difficulty_filter if difficulty_filter else original_difficulty

                # Rate limiting
                elapsed_minute = time.time() - minute_start
                if elapsed_minute < 60:
                    if minute_requests >= REQUESTS_PER_MINUTE or minute_tokens >= TOKENS_PER_MINUTE:
                        wait_time = 60 - elapsed_minute
                        time.sleep(wait_time)
                        minute_start = time.time()
                        minute_tokens = 0
                        minute_requests = 0
                else:
                    minute_start = time.time()
                    minute_tokens = 0
                    minute_requests = 0

                batch_generation_state['current_sample'] = f"{practice_area} - {topic}"

                sample, tokens_used, elapsed, error = generate_single_sample(
                    client, practice_area, topic, difficulty, current_count + i + 1, model, reasoning_instruction
                )

                if sample:
                    generated_samples.append(sample)
                    batch_generation_state['samples_generated'] += 1
                    batch_generation_state['total_tokens'] += tokens_used
                    minute_tokens += tokens_used
                    minute_requests += 1

                    # Auto-save every 10 samples
                    if len(generated_samples) % 10 == 0:
                        df_new = pl.DataFrame(generated_samples)
                        df_combined = pl.concat([df_existing, df_new])
                        df_combined.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)
                else:
                    batch_generation_state['errors'].append({
                        'topic': f"{practice_area} - {topic}",
                        'error': error
                    })

                batch_generation_state['progress'] = i + 1
                broadcast_sse_update()  # Notify SSE subscribers

                # Save to database every 10 samples
                if (i + 1) % 10 == 0:
                    save_batch_to_db(batch_generation_state)

                time.sleep(REQUEST_DELAY)

            # Final save
            if generated_samples:
                df_new = pl.DataFrame(generated_samples)
                df_combined = pl.concat([df_existing, df_new])
                df_combined.write_parquet(PARQUET_PATH, compression="zstd", statistics=True, use_pyarrow=False)

            batch_generation_state['completed_at'] = datetime.now().isoformat()
            batch_generation_state['running'] = False

            # Save final state to database
            save_batch_to_db(batch_generation_state)

        except Exception as e:
            batch_generation_state['errors'].append({'error': f"Worker error: {str(e)}"})
            batch_generation_state['running'] = False
            save_batch_to_db(batch_generation_state)
