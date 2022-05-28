from clickhouse_orm.fields import Field, Float64Field
from clickhouse_orm.utils import POINT_REGEX, RING_VALID_REGEX


class Point:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return f'<Point x={self.x} y={self.y}>'

    def to_db_string(self):
        return f'({self.x},{self.y})'


class Ring:
    def __init__(self, points):
        self.array = points

    @property
    def size(self):
        return len(self.array)

    def __len__(self):
        return len(self.array)

    def __repr__(self):
        return f'<Ring {self.to_db_string()}>'

    def to_db_string(self):
        return f'[{",".join(pt.to_db_string() for pt in self.array)}]'


def parse_point(array_string: str) -> Point:
    if len(array_string) < 2 or array_string[0] != '(' or array_string[-1] != ')':
        raise ValueError('Invalid point string: "%s"' % array_string)
    x, y = array_string.strip('()').split(',')
    return Point(x, y)


def parse_ring(array_string: str) -> Ring:
    if not RING_VALID_REGEX.match(array_string):
        raise ValueError('Invalid ring string: "%s"' % array_string)
    ring = []
    for point in POINT_REGEX.finditer(array_string):
        x, y = point.group('x'), point.group('y')
        ring.append(Point(x, y))
    return Ring(ring)


class PointField(Field):
    class_default = Point(0, 0)
    db_type = 'Point'

    def __init__(self, default=None, alias=None, materialized=None, readonly=None, codec=None,
                 db_column=None):
        super().__init__(default, alias, materialized, readonly, codec, db_column)
        self.inner_field = Float64Field()

    def to_python(self, value, timezone_in_use):
        if isinstance(value, str):
            value = parse_point(value)
        elif isinstance(value, (tuple, list)):
            if len(value) != 2:
                raise ValueError('PointField takes 2 value, but %s were given' % len(value))
            value = Point(value[0], value[1])
        if not isinstance(value, Point):
            raise ValueError('PointField expects list or tuple and Point, not %s' % type(value))
        return value

    def validate(self, value):
        pass

    def to_db_string(self, value, quote=True):
        return value.to_db_string()

    def __getitem__(self, item):
        return


class RingField(Field):
    class_default = [Point(0, 0)]
    db_type = 'Ring'

    def to_python(self, value, timezone_in_use):
        if isinstance(value, str):
            value = parse_ring(value)
        elif isinstance(value, (tuple, list)):
            ring = []
            for point in value:
                if len(point) != 2:
                    raise ValueError('Point takes 2 value, but %s were given' % len(value))
                ring.append(Point(point[0], point[1]))
            value = Ring(ring)
        if not isinstance(value, Ring):
            raise ValueError('PointField expects list or tuple and Point, not %s' % type(value))
        return value

    def to_db_string(self, value, quote=True):
        return value.to_db_string()
