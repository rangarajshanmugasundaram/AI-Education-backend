from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timezone
import math

from db_connection import db

# Target MongoDB collection for feedback records
feedback_collection = db['session_feedback']


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_feedback(request):
    """
    POST /api/feedback/submit/
    Submits student rating, review, and tags for a live class session.
    Prevents duplicate submissions from the same student for the same session.
    """
    data = request.data.copy()

    # Determine student identity
    student_id = (
            data.get('student_id') or
            request.headers.get('X-User-Email') or
            'student1@gmail.com'
    )
    student_id = str(student_id).lower().strip()
    session_id = str(data.get('session_id', 'session_101')).strip()

    # Standardize trainer ID to match dashboard query
    raw_trainer = data.get('trainer_id')
    if not raw_trainer or str(raw_trainer).strip().lower() in ['undefined', 'null', '']:
        trainer_id = 'trainer1@gmail.com'
    else:
        trainer_id = str(raw_trainer).lower().strip()

    rating = data.get('rating')
    review = str(data.get('review', '')).strip()
    tags = str(data.get('tags', 'Good')).strip()

    # Field Validations
    if not session_id:
        return Response({'error': 'session_id is a required field.'}, status=status.HTTP_400_BAD_REQUEST)

    if rating is None:
        return Response({'error': 'rating is a required field.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return Response({'error': 'Rating must be an integer between 1 and 5.'}, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        return Response({'error': 'Rating must be a valid integer.'}, status=status.HTTP_400_BAD_REQUEST)

    # Guard Against Duplicate Submissions
    existing_feedback = feedback_collection.find_one({
        'session_id': session_id,
        'student_id': student_id
    })

    if existing_feedback:
        return Response(
            {'error': 'You have already submitted feedback for this session.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Save to MongoDB
    feedback_doc = {
        'session_id': session_id,
        'student_id': student_id,
        'trainer_id': trainer_id,
        'rating': rating,
        'review': review,
        'tags': tags,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    result = feedback_collection.insert_one(feedback_doc)
    feedback_doc['_id'] = str(result.inserted_id)

    return Response(
        {'message': 'Feedback submitted successfully to MongoDB!', 'data': feedback_doc},
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_session_feedback(request, session_id):
    """
    GET /api/feedback/session/<session_id>/
    Fetches ratings, reviews, analytics, and star distribution for a session.
    """
    clean_session_id = str(session_id).strip()
    feedbacks = list(feedback_collection.find({'session_id': clean_session_id}, {'_id': 0}))

    total_reviews = len(feedbacks)
    avg_rating = round(sum(f.get('rating', 0) for f in feedbacks) / total_reviews, 1) if total_reviews > 0 else 0.0

    distribution = {str(star): 0 for star in range(1, 6)}
    for f in feedbacks:
        star_key = str(f.get('rating'))
        if star_key in distribution:
            distribution[star_key] += 1

    return Response({
        'session_id': clean_session_id,
        'metrics': {
            'average_rating': avg_rating,
            'total_reviews': total_reviews,
            'distribution': distribution,
        },
        'results': feedbacks
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_trainer_feedback(request, trainer_id):
    """
    GET /api/feedback/trainer/<trainer_id>/
    Fetches overall trainer performance metrics and review stream.
    """
    clean_trainer_id = str(trainer_id).lower().strip()
    feedbacks = list(feedback_collection.find({'trainer_id': clean_trainer_id}, {'_id': 0}))

    total_reviews = len(feedbacks)
    avg_rating = round(sum(f.get('rating', 0) for f in feedbacks) / total_reviews, 1) if total_reviews > 0 else 0.0

    distribution = {str(star): 0 for star in range(1, 6)}
    for f in feedbacks:
        star_key = str(f.get('rating'))
        if star_key in distribution:
            distribution[star_key] += 1

    return Response({
        'trainer_id': clean_trainer_id,
        'metrics': {
            'overall_rating': avg_rating,
            'total_reviews': total_reviews,
            'distribution': distribution,
        },
        'results': feedbacks
    }, status=status.HTTP_200_OK)