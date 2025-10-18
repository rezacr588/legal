"""
Data API Routes - PostgreSQL-backed endpoints for legal samples.

All routes use DataService for ORM-based database access.
"""

from flask import Blueprint, jsonify, request
from services.data_service import DataService
from models import db

# Create blueprint
data_bp = Blueprint('data', __name__, url_prefix='/api')


@data_bp.route('/data')
def get_data():
    """Get all samples from PostgreSQL database."""
    try:
        # Get pagination parameters
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', default=0, type=int)

        service = DataService()
        samples = service.get_all(limit=limit, offset=offset)

        return jsonify(samples)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/stats')
def get_stats():
    """Get dataset statistics from PostgreSQL."""
    try:
        service = DataService()
        stats = service.get_stats()

        return jsonify(stats)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/add', methods=['POST'])
def add_sample():
    """Add a new sample to PostgreSQL."""
    try:
        data = request.json

        service = DataService()
        sample = service.add(data)

        return jsonify({
            'success': True,
            'sample': sample,
            'total_samples': service.count()
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/import/jsonl', methods=['POST'])
def import_jsonl():
    """Import multiple samples from JSONL content."""
    try:
        data = request.json
        jsonl_content = data.get('content', '')

        if not jsonl_content:
            return jsonify({'success': False, 'error': 'No JSONL content provided'}), 400

        # Parse JSONL
        import json
        samples = []
        lines = jsonl_content.strip().split('\n')

        for idx, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                return jsonify({
                    'success': False,
                    'error': f'Line {idx}: Invalid JSON - {str(e)}'
                }), 400

        if not samples:
            return jsonify({'success': False, 'error': 'No valid samples found'}), 400

        # Add samples using DataService
        service = DataService()
        result = service.add_bulk(samples)

        if result['errors']:
            return jsonify({
                'success': False,
                'error': f"Failed to import some samples",
                'added': result['added'],
                'errors': result['errors']
            }), 400

        return jsonify({
            'success': True,
            'message': f'Successfully imported {result["added"]} samples',
            'total_samples': service.count()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/sample/<sample_id>', methods=['GET'])
def get_sample(sample_id):
    """Get a single sample by ID."""
    try:
        service = DataService()
        sample = service.get_by_id(sample_id)

        if not sample:
            return jsonify({
                'success': False,
                'error': f'Sample with ID "{sample_id}" not found'
            }), 404

        return jsonify({'success': True, 'sample': sample})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/sample/<sample_id>', methods=['PUT'])
def update_sample(sample_id):
    """Update an existing sample."""
    try:
        data = request.json

        service = DataService()
        sample = service.update(sample_id, data)

        return jsonify({
            'success': True,
            'message': f'Sample {sample_id} updated successfully',
            'sample': sample,
            'total_samples': service.count()
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/sample/<sample_id>', methods=['DELETE'])
def delete_sample(sample_id):
    """Delete a sample."""
    try:
        service = DataService()
        deleted = service.delete(sample_id)

        if not deleted:
            return jsonify({
                'success': False,
                'error': f'Sample with ID "{sample_id}" not found'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Sample {sample_id} deleted successfully',
            'total_samples': service.count()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/search')
def search_samples():
    """Full-text search across samples."""
    try:
        query = request.args.get('q', default='', type=str)
        field = request.args.get('field', default='all', type=str)
        limit = request.args.get('limit', default=100, type=int)

        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter "q" is required'
            }), 400

        service = DataService()
        results = service.search(query, field=field, limit=limit)

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'query': query,
            'field': field
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/samples/random')
def get_random_samples():
    """Get random samples."""
    try:
        count = request.args.get('count', default=5, type=int)
        difficulty = request.args.get('difficulty', default=None, type=str)

        service = DataService()
        samples = service.get_random(count=count, difficulty=difficulty)

        return jsonify({
            'success': True,
            'samples': samples,
            'count': len(samples)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/samples/filter')
def get_filtered_samples():
    """Get samples matching filter criteria."""
    try:
        topic = request.args.get('topic', type=str)
        difficulty = request.args.get('difficulty', type=str)
        jurisdiction = request.args.get('jurisdiction', type=str)
        sample_type = request.args.get('sample_type', type=str)
        limit = request.args.get('limit', type=int)

        service = DataService()
        samples = service.get_filtered(
            topic=topic,
            difficulty=difficulty,
            jurisdiction=jurisdiction,
            sample_type=sample_type,
            limit=limit
        )

        return jsonify({
            'success': True,
            'samples': samples,
            'count': len(samples),
            'filters': {
                'topic': topic,
                'difficulty': difficulty,
                'jurisdiction': jurisdiction,
                'sample_type': sample_type
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/batch/<batch_id>/samples')
def get_batch_samples(batch_id):
    """Get all samples from a specific batch."""
    try:
        service = DataService()
        samples = service.get_by_batch(batch_id)

        if not samples:
            return jsonify({
                'success': False,
                'error': f'No samples found for batch ID "{batch_id}"'
            }), 404

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'samples': samples,
            'count': len(samples)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/batch/<batch_id>/quality')
def get_batch_quality(batch_id):
    """Get quality metrics for samples from a specific batch."""
    try:
        import tiktoken
        from collections import Counter

        service = DataService()
        samples = service.get_by_batch(batch_id)

        if not samples:
            return jsonify({
                'success': False,
                'error': f'No samples found for batch ID "{batch_id}"'
            }), 404

        # Initialize tiktoken encoder
        enc = tiktoken.get_encoding("cl100k_base")

        def count_tokens(text):
            if not text or not isinstance(text, str):
                return 0
            return len(enc.encode(text))

        # Calculate metrics
        total_samples = len(samples)
        total_tokens = 0
        difficulties = []
        topics = []
        sample_types = []
        jurisdictions = []

        answer_lengths = []
        reasoning_lengths = []
        citation_lengths = []

        for sample in samples:
            # Token counting
            sample_tokens = sum([
                count_tokens(sample.get('question', '')),
                count_tokens(sample.get('answer', '')),
                count_tokens(sample.get('reasoning', '')),
                count_tokens(sample.get('case_citation', ''))
            ])
            total_tokens += sample_tokens

            # Distributions
            difficulties.append(sample.get('difficulty', 'unknown'))
            topics.append(sample.get('topic', 'unknown'))
            if sample.get('sample_type'):
                sample_types.append(sample.get('sample_type'))
            if sample.get('jurisdiction'):
                jurisdictions.append(sample.get('jurisdiction'))

            # Quality metrics
            answer_lengths.append(len(sample.get('answer', '')))
            reasoning_lengths.append(len(sample.get('reasoning', '')))
            citation_lengths.append(len(sample.get('case_citation', '')))

        # Calculate averages
        avg_tokens = total_tokens / total_samples if total_samples > 0 else 0
        avg_answer_length = sum(answer_lengths) / total_samples if total_samples > 0 else 0
        avg_reasoning_length = sum(reasoning_lengths) / total_samples if total_samples > 0 else 0
        avg_citation_length = sum(citation_lengths) / total_samples if total_samples > 0 else 0

        # Distribution counts
        difficulty_dist = Counter(difficulties)
        topic_dist = Counter(topics)
        sample_type_dist = Counter(sample_types) if sample_types else {}
        jurisdiction_dist = Counter(jurisdictions) if jurisdictions else {}

        # Quality flags
        quality_issues = []
        if avg_answer_length < 300:
            quality_issues.append('Short answers (avg < 300 chars)')
        if avg_reasoning_length < 100:
            quality_issues.append('Short reasoning (avg < 100 chars)')
        if avg_citation_length < 50:
            quality_issues.append('Short citations (avg < 50 chars)')

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'metrics': {
                'total_samples': total_samples,
                'total_tokens': total_tokens,
                'avg_tokens_per_sample': round(avg_tokens, 2),
                'avg_answer_length': round(avg_answer_length, 2),
                'avg_reasoning_length': round(avg_reasoning_length, 2),
                'avg_citation_length': round(avg_citation_length, 2)
            },
            'distributions': {
                'difficulty': dict(difficulty_dist),
                'topics': dict(topic_dist),
                'sample_types': dict(sample_type_dist),
                'jurisdictions': dict(jurisdiction_dist)
            },
            'quality_score': {
                'issues': quality_issues,
                'rating': 'Good' if len(quality_issues) == 0 else 'Needs Review'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# DOWNLOAD ENDPOINTS
# ============================================================================

@data_bp.route('/sample/<sample_id>/download', methods=['GET'])
def download_sample(sample_id):
    """Download a single sample as a JSON file."""
    try:
        import json
        from flask import make_response

        service = DataService()
        sample = service.get_by_id(sample_id)

        if not sample:
            return jsonify({
                'success': False,
                'error': f'Sample with ID "{sample_id}" not found'
            }), 404

        # Create JSON string with proper formatting
        json_str = json.dumps(sample, indent=2, ensure_ascii=False)

        # Create response with download headers
        response = make_response(json_str)
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename="{sample_id}.json"'

        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/samples/download', methods=['POST'])
def download_samples():
    """Download multiple samples as a JSONL file."""
    try:
        import json
        from flask import make_response

        data = request.json
        sample_ids = data.get('sample_ids', [])

        if not sample_ids:
            return jsonify({
                'success': False,
                'error': 'No sample IDs provided'
            }), 400

        # Get samples from database
        service = DataService()
        samples = []
        for sample_id in sample_ids:
            sample = service.get_by_id(sample_id)
            if sample:
                samples.append(sample)

        if not samples:
            return jsonify({
                'success': False,
                'error': 'No samples found with provided IDs'
            }), 404

        # Create JSONL string (one JSON object per line)
        jsonl_lines = [json.dumps(sample, ensure_ascii=False) for sample in samples]
        jsonl_str = '\n'.join(jsonl_lines)

        # Create response with download headers
        response = make_response(jsonl_str)
        response.headers['Content-Type'] = 'application/x-ndjson'
        response.headers['Content-Disposition'] = f'attachment; filename="samples_{len(samples)}.jsonl"'

        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# DETAILED STATISTICS ENDPOINTS
# ============================================================================

@data_bp.route('/stats/detailed')
def get_detailed_stats():
    """Get detailed dataset statistics with comprehensive breakdowns."""
    try:
        from sqlalchemy import func
        from models import LegalSample

        service = DataService()

        # Get basic stats
        total_samples = service.count()

        # Difficulty breakdown with averages
        difficulty_breakdown = db.session.query(
            LegalSample.difficulty,
            func.count(LegalSample.id).label('count'),
            func.avg(func.length(LegalSample.question)).label('avg_question_length'),
            func.avg(func.length(LegalSample.answer)).label('avg_answer_length')
        ).group_by(LegalSample.difficulty).all()

        # Topic breakdown
        topic_breakdown = db.session.query(
            LegalSample.topic,
            func.count(LegalSample.id).label('count')
        ).group_by(LegalSample.topic).order_by(
            func.count(LegalSample.id).desc()
        ).all()

        # Practice areas (extract from topic)
        practice_areas = db.session.query(
            func.split_part(LegalSample.topic, ' - ', 1).label('practice_area'),
            func.count(LegalSample.id).label('count')
        ).group_by('practice_area').order_by(
            func.count(LegalSample.id).desc()
        ).all()

        # Average lengths
        avg_lengths = db.session.query(
            func.avg(func.length(LegalSample.question)).label('question'),
            func.avg(func.length(LegalSample.answer)).label('answer'),
            func.avg(func.length(LegalSample.reasoning)).label('reasoning'),
            func.avg(func.length(LegalSample.case_citation)).label('case_citation')
        ).first()

        # Unique counts
        unique_topics = db.session.query(
            func.count(func.distinct(LegalSample.topic))
        ).scalar()

        unique_practice_areas = db.session.query(
            func.count(func.distinct(func.split_part(LegalSample.topic, ' - ', 1)))
        ).scalar()

        stats = {
            'total_samples': total_samples,
            'difficulty_breakdown': [
                {
                    'difficulty': d.difficulty,
                    'count': d.count,
                    'avg_question_length': round(d.avg_question_length or 0, 2),
                    'avg_answer_length': round(d.avg_answer_length or 0, 2)
                }
                for d in difficulty_breakdown
            ],
            'topic_breakdown': [
                {'topic': t.topic, 'count': t.count}
                for t in topic_breakdown
            ],
            'practice_areas': [
                {'practice_area': pa.practice_area, 'count': pa.count}
                for pa in practice_areas
            ],
            'avg_lengths': {
                'question': round(avg_lengths.question or 0, 2),
                'answer': round(avg_lengths.answer or 0, 2),
                'reasoning': round(avg_lengths.reasoning or 0, 2),
                'case_citation': round(avg_lengths.case_citation or 0, 2)
            },
            'unique_topics': unique_topics,
            'unique_practice_areas': unique_practice_areas
        }

        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@data_bp.route('/stats/tokens')
def get_token_stats():
    """Get comprehensive token statistics for the dataset."""
    try:
        import tiktoken
        from models import LegalSample

        service = DataService()
        samples = service.get_all()

        # Initialize tiktoken encoder (GPT-4 encoding)
        enc = tiktoken.get_encoding("cl100k_base")

        def count_tokens(text):
            if not text or not isinstance(text, str):
                return 0
            return len(enc.encode(text))

        # Calculate total tokens and per-field breakdown
        total_tokens = 0
        field_tokens = {
            'question': 0,
            'answer': 0,
            'reasoning': 0,
            'case_citation': 0,
            'topic': 0
        }

        for sample in samples:
            for field in field_tokens.keys():
                tokens = count_tokens(sample.get(field, ''))
                field_tokens[field] += tokens
                total_tokens += tokens

        num_samples = len(samples)
        avg_tokens_per_sample = total_tokens / num_samples if num_samples > 0 else 0

        # Calculate tokens by difficulty
        tokens_by_difficulty = {}
        difficulty_samples = {}

        for sample in samples:
            difficulty = sample.get('difficulty', 'unknown')
            if difficulty not in difficulty_samples:
                difficulty_samples[difficulty] = []
            difficulty_samples[difficulty].append(sample)

        for difficulty, diff_samples in difficulty_samples.items():
            difficulty_tokens = 0
            for sample in diff_samples:
                for field in ['question', 'answer', 'reasoning', 'case_citation', 'topic']:
                    difficulty_tokens += count_tokens(sample.get(field, ''))

            tokens_by_difficulty[difficulty] = {
                'total_tokens': difficulty_tokens,
                'avg_tokens': difficulty_tokens / len(diff_samples) if diff_samples else 0,
                'sample_count': len(diff_samples)
            }

        # Calculate tokens by practice area (top 10)
        practice_area_tokens = {}
        for sample in samples:
            topic = sample.get('topic', '')
            if ' - ' in topic:
                practice_area = topic.split(' - ')[0]
            else:
                practice_area = topic

            if practice_area not in practice_area_tokens:
                practice_area_tokens[practice_area] = {'tokens': 0, 'count': 0}

            sample_tokens = sum(
                count_tokens(sample.get(field, ''))
                for field in ['question', 'answer', 'reasoning', 'case_citation', 'topic']
            )
            practice_area_tokens[practice_area]['tokens'] += sample_tokens
            practice_area_tokens[practice_area]['count'] += 1

        # Sort and limit to top 10 practice areas
        sorted_practice_areas = sorted(
            [
                {
                    'practice_area': k,
                    'total_tokens': v['tokens'],
                    'avg_tokens': v['tokens'] / v['count'],
                    'count': v['count']
                }
                for k, v in practice_area_tokens.items()
            ],
            key=lambda x: x['total_tokens'],
            reverse=True
        )[:10]

        # Estimated costs for Groq API models
        model_pricing = {
            'llama-3.3-70b': {'price_per_1m': 0.69, 'name': 'Llama 3.3 70B (Groq)'},
            'llama-3.1-70b': {'price_per_1m': 0.69, 'name': 'Llama 3.1 70B (Groq)'},
            'llama-3.1-8b': {'price_per_1m': 0.065, 'name': 'Llama 3.1 8B (Groq)'},
            'mixtral-8x7b': {'price_per_1m': 0.24, 'name': 'Mixtral 8x7B (Groq)'},
            'gemma-7b': {'price_per_1m': 0.07, 'name': 'Gemma 7B (Groq)'}
        }

        estimated_costs = {}
        for model_id, pricing in model_pricing.items():
            cost = (total_tokens / 1_000_000) * pricing['price_per_1m']
            estimated_costs[model_id] = {
                'name': pricing['name'],
                'cost_usd': round(cost, 4),
                'price_per_1m': pricing['price_per_1m']
            }

        return jsonify({
            'success': True,
            'stats': {
                'total_tokens': total_tokens,
                'total_samples': num_samples,
                'avg_tokens_per_sample': round(avg_tokens_per_sample, 2),
                'tokens_by_field': {
                    field: {
                        'total': tokens,
                        'avg_per_sample': round(tokens / num_samples, 2) if num_samples > 0 else 0,
                        'percentage': round((tokens / total_tokens * 100), 2) if total_tokens > 0 else 0
                    }
                    for field, tokens in field_tokens.items()
                },
                'tokens_by_difficulty': tokens_by_difficulty,
                'tokens_by_practice_area': sorted_practice_areas,
                'estimated_costs': estimated_costs,
                'encoding': 'cl100k_base (GPT-4 tokenizer)'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# HUGGINGFACE HUB INTEGRATION
# ============================================================================

@data_bp.route('/huggingface/push', methods=['POST', 'OPTIONS'])
def push_to_huggingface():
    """Push dataset to Hugging Face Hub."""
    import json
    from pathlib import Path

    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        return '', 200

    try:
        from huggingface_hub import HfApi, create_repo
        from models import Provider, ProviderConfig

        data = request.json

        # SECURITY: Load HuggingFace token from encrypted database
        # Token can be provided in request (optional) or loaded from database
        token = data.get('token')
        if not token:
            # Load from encrypted database
            hf_provider = Provider.query.filter_by(id='huggingface').first()
            if hf_provider and hf_provider.config:
                token = hf_provider.config.get_api_key()

        repo_name = data.get('repo_name', 'legal-training-dataset')
        format_type = data.get('format', 'parquet')
        is_private = data.get('private', False)

        if not token:
            return jsonify({
                'success': False,
                'error': 'Hugging Face token is required. Configure it in Provider Manager or provide in request.'
            }), 400

        # Initialize Hugging Face API
        api = HfApi()

        # Get username
        user_info = api.whoami(token=token)
        username = user_info['name']
        repo_id = f"{username}/{repo_name}"

        # Create repository if it doesn't exist
        try:
            create_repo(
                repo_id=repo_id,
                token=token,
                repo_type="dataset",
                private=is_private,
                exist_ok=True
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to create repository: {str(e)}'
            }), 400

        # Get all samples from database
        service = DataService()
        samples = service.get_all()

        # Prepare file for upload
        temp_dir = Path("/tmp/hf_upload")
        temp_dir.mkdir(exist_ok=True)

        if format_type == 'parquet':
            # Export to parquet
            import polars as pl
            df = pl.DataFrame(samples)
            file_path = temp_dir / "train.parquet"
            df.write_parquet(file_path, compression="zstd")

        elif format_type == 'json':
            # Export to JSON
            file_path = temp_dir / "train.json"
            with open(file_path, 'w') as f:
                json.dump(samples, f, indent=2)

        elif format_type == 'csv':
            # Export to CSV
            import polars as pl
            df = pl.DataFrame(samples)
            file_path = temp_dir / "train.csv"
            df.write_csv(file_path)

        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format_type}'
            }), 400

        # Upload file
        api.upload_file(
            path_or_fileobj=str(file_path),
            path_in_repo=f"train.{format_type}",
            repo_id=repo_id,
            repo_type="dataset",
            token=token
        )

        # Clean up temp file
        file_path.unlink()

        return jsonify({
            'success': True,
            'message': f'Successfully pushed to Hugging Face',
            'repo_url': f'https://huggingface.co/datasets/{repo_id}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
