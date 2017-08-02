import uuid

from valet.api.db.models import music as models


def group(name="mock_group", description="mock group", type="affinity",
          level="host", members='["test_tenant_id"]'):
    """Boilerplate for creating a group"""
    group = models.Group(name=name, description=description, type=type,
                         level=level, members=members, _insert=False)
    group.id = str(uuid.uuid4())
    return group
