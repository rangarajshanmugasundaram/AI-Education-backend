from rest_framework import serializers


class NotificationSerializer(serializers.Serializer):
  id = serializers.CharField(read_only=True)
  title = serializers.CharField(max_length=255, required=True)
  message = serializers.CharField(required=True)
  sender_id = serializers.EmailField(required=False)
  sender_role = serializers.CharField(max_length=50, required=False)
  recipient_type = serializers.ChoiceField(
      choices=['All', 'Batch', 'User'], default='All'
  )
  recipient_id = serializers.CharField(
      required=False, allow_null=True, allow_blank=True
  )
  batch_id = serializers.CharField(
      required=False, allow_null=True, allow_blank=True
  )
  priority = serializers.ChoiceField(
      choices=['Low', 'Medium', 'High'], default='Medium'
  )
  read_status = serializers.BooleanField(default=False)
  created_at = serializers.CharField(read_only=True)
  updated_at = serializers.CharField(read_only=True)

  def validate(self, data):
    recipient_type = data.get('recipient_type')
    if recipient_type == 'User' and not data.get('recipient_id'):
      raise serializers.ValidationError({
          'recipient_id': (
              'Recipient Email is required when recipient_type is User.'
          )
      })
    if recipient_type == 'Batch' and not data.get('batch_id'):
      raise serializers.ValidationError({
          'batch_id': 'Batch ID is required when recipient_type is Batch.'
      })
    return data