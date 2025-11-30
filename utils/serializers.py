def serialise_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'forename': user.forename,
        'default_group_id': user.default_group_id
    }

serialise_model = lambda model: {col.name: getattr(model, col.name) for col in model.__table__.columns}
