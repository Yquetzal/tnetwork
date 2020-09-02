"""'fig' module - object-oriented interface to XFig files.

You can read fig files into a `File` object 'f' with::

  import fig
  f = fig.File(filename) # or pass a file-like object"""

__author__ = "Hans Meine <hans_meine@gmx.net>"
__version__ = "0.9"

import sys, re, math, os, operator, copy

from named_constants import Constants


class FigConstants(Constants):
    @classmethod
    def read(cls, i):
        return cls(int(i))


class ObjectType(FigConstants):
    CustomColor = 0
    Ellipse = 1
    Polygon = 2
    Spline = 3
    Text = 4
    Arc = 5
    CompoundBegin = 6
    CompoundEnd = -6


class PolygonType(FigConstants):
    """cf. `PolylineBase.changeType()`"""
    Polyline = 1
    Box = 2
    Polygon = 3
    ArcBox = 4
    PictureBBox = 5


class EllipseType(FigConstants):
    """cf. `EllipseBase.changeType()`"""
    EllipseRadii = 1
    EllipseDiameter = 2
    CircleRadius = 3
    CircleDiameter = 4


class SplineType(FigConstants):
    """cf. `SplineBase.changeType()`"""
    OpenApproximated = 0
    ClosedApproximated = 1
    OpenInterpolated = 2
    ClosedInterpolated = 3
    OpenXSpline = 4
    ClosedXSpline = 5


class ArcType(FigConstants):
    """cf. `ArcBase.changeType()`"""
    Open = 1
    Pie = 2


class ArcDirection(FigConstants):
    """cf. ArcBase.direction property"""
    Clockwise = 0
    CounterClockwise = 1


class FillStyle(FigConstants):
    """cf. `Object.fillStyle` property"""
    None_ = -1
    Black = 0
    Shaded5 = 1
    Shaded10 = 2
    Shaded15 = 3
    Shaded20 = 4
    Shaded25 = 5
    Shaded30 = 6
    Shaded35 = 7
    Shaded40 = 8
    Shaded45 = 9
    Shaded50 = 10
    Shaded55 = 11
    Shaded60 = 12
    Shaded65 = 13
    Shaded70 = 14
    Shaded75 = 15
    Shaded80 = 16
    Shaded85 = 17
    Shaded90 = 18
    Shaded95 = 19
    Solid = 20
    Tinted95 = 21
    Tinted90 = 22
    Tinted85 = 23
    Tinted80 = 24
    Tinted75 = 25
    Tinted70 = 26
    Tinted65 = 27
    Tinted60 = 28
    Tinted55 = 29
    Tinted50 = 30
    Tinted45 = 31
    Tinted40 = 32
    Tinted35 = 33
    Tinted30 = 34
    Tinted25 = 35
    Tinted20 = 36
    Tinted15 = 37
    Tinted10 = 38
    Tinted5 = 39
    White = 40
    Left30 = 41
    "30 degree left diagonal pattern"
    Right30 = 42
    "30 degree right diagonal pattern"
    Crossed30 = 43
    "30 degree cross-hatched pattern"
    Left45 = 44
    "45 degree left diagonal pattern"
    Right45 = 45
    "45 degree right diagonal pattern"
    Crossed45 = 46
    "45 degree cross-hatched pattern"
    HorizontalBricks = 47
    "horizontal bricks pattern"
    VerticalBricks = 48
    "vertical bricks pattern"
    HorizontalLines = 49
    "horizontal lines pattern"
    VerticalLines = 50
    "vertical lines pattern"
    Crosshatch = 51
    "crosshatch pattern"
    HorizontalShingles1 = 52
    "horizontal \"shingles\" pattern skewed to the right"
    HorizontalShingles2 = 53
    "horizontal \"shingles\" pattern skewed to the left"
    VerticalShingles1 = 54
    "vertical \"shingles\" pattern skewed one way"
    VerticalShingles2 = 55
    "vertical \"shingles\" pattern skewed the other way"
    FishScales = 56
    "fish scales pattern"
    SmallFishScales = 57
    "small fish scales pattern"
    Circles = 58
    "circles pattern"
    Hexagons = 59
    "hexagons pattern"
    Octagons = 60
    "octagons pattern"
    HorizontalTireTreads = 61
    "horizontal \"tire treads\" pattern"
    VerticalTireTreads = 62
    "vertical \"tire treads\" pattern"

    def shaded(percent):
        """Return a fillStyle for dark shades of the fill color.
        `percent` decides between 0 = black .. 100 = fillColor (5% steps)"""
        return FillStyle(int(round(percent / 5.0)))

    def tinted(percent):
        """Return a fillStyle for light tinted fill colors.
        `percent` decides between 0 = white .. 100 = fillColor (5% steps)"""
        return FillStyle(40 - int(round(percent / 5.0)))


class ArrowType(FigConstants):
    """cf. `Arrow` class"""
    Stick = 0
    "stick-type, three-stroke arrow head (default in xfig 2.1 and earlier)"
    Closed = 1
    "closed triangle"
    ClosedIndented = 2
    "closed with 'indented' butt"
    ClosedPointed = 3
    "closed with 'pointed' butt"
    ClosedDiamond = 4
    "closed parallelogram"
    ClosedCircle = 5
    "closed circle"
    HalfCircle = 6
    "open half-circle"
    ClosedRectangle = 7
    "closed rectangle"
    ClosedReverse = 8
    "closed reverse triangle"
    HalfFilled = 9
    "half-filled triangle (side determined by arrow style)"
    RightHalf = 10
    "right half of closed triangle"
    RightHalfIndented = 11
    "right half of triangle with 'indented' butt"
    RightHalfIndented = 12
    "right half of triangle with 'pointed' butt"
    ReversedStick = 13
    "open reversed triangle (alternate style: perpendicular line)"
    OpenRectangle = 14
    "open rectangle (direction determined by arrow style)"


class ArrowStyle(FigConstants):
    """cf. `Arrow` class"""
    Hollow = 0
    "filled with white"
    Filled = 1
    "filled with penColor"


class LineStyle(FigConstants):
    """cf. `Object.lineStyle` property"""
    Default = -1
    Solid = 0
    Dashed = 1
    Dotted = 2
    DashDotted = 3
    DashDoubleDotted = 4
    DashTripleDotted = 5


class CapStyle(FigConstants):
    """cf. `Object.capStyle` property, used by Polyline, OpenArc, and open splines"""
    Butt = 0
    Round = 1
    Projecting = 2


class JoinStyle(FigConstants):
    """cf. `Object.joinStyle` property, used for `Polyline` objects only"""
    Miter = 0
    Round = 1
    Bevel = 2


standardColors = [
    # pure colors:
    (0, 0, 0),
    (0, 0, 255),
    (0, 255, 0),
    (0, 255, 255),
    (255, 0, 0),
    (255, 0, 255),
    (255, 255, 0),
    (255, 255, 255),
    # four blues:
    (0, 0, 144),
    (0, 0, 176),
    (0, 0, 208),
    (135, 206, 255),
    # three greens:
    (0, 144, 0),
    (0, 176, 0),
    (0, 208, 0),
    # three cyans:
    (0, 144, 144),
    (0, 176, 176),
    (0, 208, 208),
    # three reds:
    (144, 0, 0),
    (176, 0, 0),
    (208, 0, 0),
    # three magentas:
    (144, 0, 144),
    (176, 0, 176),
    (208, 0, 208),
    # three browns:
    (128, 48, 0),
    (160, 64, 0),
    (192, 96, 0),
    # four pinks:
    (255, 128, 128),
    (255, 160, 160),
    (255, 192, 192),
    (255, 224, 224),
    # gold:
    (255, 215, 0),
]
"Mapping of the standard colors to RGB triples."


class Color(Constants):
    """cf. `Object.penColor` and `Object.fillColor` properties"""
    Default = -1
    Black = 0
    Blue = 1
    Green = 2
    Cyan = 3
    Red = 4
    Magenta = 5
    Yellow = 6
    White = 7
    Blue4 = 8
    Blue3 = 9
    Blue2 = 10
    LightBlue = 11
    Green4 = 12
    Green3 = 13
    Green2 = 14
    Cyan4 = 15
    Cyan3 = 16
    Cyan2 = 17
    Red4 = 18
    Red3 = 19
    Red2 = 20
    Magenta4 = 21
    Magenta3 = 22
    Magenta2 = 23
    Brown4 = 24
    Brown3 = 25
    Brown2 = 26
    Pink4 = 27
    Pink3 = 28
    Pink2 = 29
    LightPink = 30
    Gold = 31
    Custom0 = 32

    @classmethod
    def read(cls, i):
        i = int(i)
        if i <= Color.Custom0:
            return Color(i)
        return i


class Alignment(FigConstants):
    """cf. `Text.alignment` property"""
    Left = 0
    Centered = 1
    Right = 2


class Font(FigConstants):
    """cf. `Text.font` property, only valid if `Text.fontFlags` & FontFlag.PostScript"""
    Default = -1
    TimesRoman = 0
    TimesItalic = 1
    TimesBold = 2
    TimesBoldItalic = 3
    AvantGardeBook = 4
    AvantGardeBookOblique = 5
    AvantGardeDemi = 6
    AvantGardeDemiOblique = 7
    BookmanLight = 8
    BookmanLightItalic = 9
    BookmanDemi = 10
    BookmanDemiItalic = 11
    Courier = 12
    CourierOblique = 13
    CourierBold = 14
    CourierBoldOblique = 15
    Helvetica = 16
    HelveticaOblique = 17
    HelveticaBold = 18
    HelveticaBoldOblique = 19
    HelveticaNarrow = 20
    HelveticaNarrowOblique = 21
    HelveticaNarrowBold = 22
    HelveticaNarrowBoldOblique = 23
    NewCenturySchoolbookRoman = 24
    NewCenturySchoolbookItalic = 25
    NewCenturySchoolbookBold = 26
    NewCenturySchoolbookBoldItalic = 27
    PalatinoRoman = 28
    PalatinoItalic = 29
    PalatinoBold = 30
    PalatinoBoldItalic = 31
    Symbol = 32
    ZapfChanceryMediumItalic = 33
    ZapfDingbats = 34


class LaTeXFont(FigConstants):
    """cf. `Text.font` property, only valid if `Text.fontFlags` & FontFlag.PostScript == 0"""
    LaTeXDefault = 0
    LaTeXRoman = 1
    LaTeXBold = 2
    LaTeXItalic = 3
    LaTeXSansSerif = 4
    LaTeXTypewriter = 5


class FontFlag(Constants):
    """cf. `Text.fontFlags` property"""
    Rigid = 1
    Special = 2
    PostScript = 4
    Hidden = 8


paperSizes = ["Letter", "Legal", "Ledger", "Tabloid",
              "A", "B", "C", "D", "E",
              "A4", "A3", "A2", "A1", "A0", "B5"]
"""Valid paper sizes, cf. `File.paperSize`."""

unitCM = 450
"""fig units per centimeter (used for positions, radii, ...)"""


# --------------------------------------------------------------------
#                              helpers
# --------------------------------------------------------------------

def _join(*sequence):
    """Helper function to bring internal object parameters into XFig
    string format.  Attention: floating point numbers are rounded and
    converted to integer - if floats are to be output, call str() on
    them before passing to this function."""
    parts = []
    for item in sequence:
        if isinstance(item, float):
            parts.append(str(int(round(item))))
        elif isinstance(item, bool):
            parts.append(str(int(item)))
        else:
            parts.append(str(item))
    return " ".join(parts)


def _formatComment(comment):
    if not comment:
        return ""
    result = ["#" + c for c in comment.split("\n")]
    if result[-1] == "#":
        result[-1] = ""
    else:
        result.append("")
    return "\n".join(result)


_re_size = re.compile("([0-9]+)x([0-9]+)")
_re_geometry = re.compile("([0-9]+)[:,]([0-9]+)([+-:,])([0-9]+)([x:,])([0-9]+)")


def parseSize(sizeStr):
    """Convenience function for parsing size strings into tuples:

      >>> fig.parseSize('640x480')
      (640, 480)
    """
    ma = _re_size.match(sizeStr)
    if ma:
        w = int(ma.group(1))
        h = int(ma.group(2))
        return (w, h)


def parseGeometry(geometryString):
    """Convenience function for parsing geometry strings of various
    formats.  Example usage:

    >>> fig.parseGeometry("320,240-640,480")
    fig.Rect(320,240,640,480)
    >>> fig.parseGeometry("50,50+50,50")
    fig.Rect(50,50,100,100)
    >>> fig.parseGeometry("40,40,320,240")
    fig.Rect(40,40,320,240)
    >>> r = fig.Rect(0,0,320,240)
    >>> fig.parseGeometry(str(r)) == r
    True
    """
    ma = _re_geometry.match(geometryString)
    if ma:
        x1 = int(ma.group(1))
        y1 = int(ma.group(2))
        vx2 = int(ma.group(4))
        vy2 = int(ma.group(6))
        if ma.group(3) == "+" or ma.group(5) == "x":
            assert ma.group(
                3) != "-", "invalid geometry string format 'X,Y-WxH': %s (use either x1,y2-x2,y2 *or* x1,y1+WxH)" % geometryString
            return Rect(x1, y1, x1 + vx2, y1 + vy2)
        else:
            return Rect(x1, y1, vx2, vy2)


class Vector(object):
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, index):
        if index == 0 or index == -2:
            return self.x
        if index == 1 or index == -1:
            return self.y
        raise IndexError("Vector only has two components")

    def __setitem__(self, index, value):
        if index == 0 or index == -2:
            self.x = value
        elif index == 1 or index == -1:
            self.y = value
        else:
            raise IndexError("Vector only has two components")

    def __mul__(self, s):
        return Vector(self[0] * s, self[1] * s)

    __rmul__ = __mul__

    def __div__(self, s):
        return Vector(self[0] / s, self[1] / s)

    def __add__(self, other):
        return Vector(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other):
        return Vector(self[0] - other[0], self[1] - other[1])

    def dot(self, other):
        return self[0] * other[0] + self[1] * other[1]

    def length2(self):
        return self.dot(self)

    def length(self):
        return math.sqrt(self.length2())

    def normalized(self):
        return self / self.length()

    def dist(self, other):
        return (self - other).length()

    def __len__(self):
        return 2

    def __eq__(self, other):
        try:
            if len(other) != 2:
                return False
        except TypeError:  # "len() of unsized object"
            return False
        return self[0] == other[0] and self[1] == other[1]

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "fig.Vector(%s, %s)" % (self.x, self.y)


class Rect(object):
    """This is a simple, half-internal helper class for handling
    Rectangles (e.g. used for bounding boxes).  If you are looking for
    a rectangular figure object, `PolyBox` is your friend.

    A Rect object has the properties `x1`, `x2`, `y1`, `y2` carrying
    the coordinates, and accessor functions `width()`, `height()`,
    `upperLeft()`, `lowerRight()`, `center()`, `size()`.  (The latter
    return pairs of coordinates.)

    A special facility is the __call__ operator for adding
    points/rects (sort of a UNION operation).

    Finally, it is possible to do::

      x1, y1, x2, y2 = someRect"""

    __slots__ = ("x1", "y1", "x2", "y2",
                 "_empty")

    def __init__(self, *args):
        assert len(args) in (0, 4), \
            "Rect.__init__() expecting zero or four parameters!"
        if len(args) == 4:
            self.x1, self.y1, self.x2, self.y2 = args
            self._empty = False
        else:
            self._empty = True

    def __call__(self, other):
        if isinstance(other, Rect):
            if other._empty:
                return
            self.__call__((other.x1, other.y1))
            self.__call__((other.x2, other.y2))
        else:
            if self._empty:
                self.x1 = other[0]
                self.x2 = other[0]
                self.y1 = other[1]
                self.y2 = other[1]
                self._empty = False
            else:
                self.x1 = min(self.x1, other[0])
                self.y1 = min(self.y1, other[1])
                self.x2 = max(self.x2, other[0])
                self.y2 = max(self.y2, other[1])

    def contains(self, other):
        """Return True iff other is a Rect or point that is entirely
        within this Rect.  (Points on the border are considered to be
        contained.)"""
        if isinstance(other, Rect):
            return other.empty() or (
                    self.contains(other.upperLeft()) and
                    self.contains(other.lowerRight()))
        return ((self.x1 <= other[0]) and (self.y1 <= other[1]) and
                (other[0] <= self.x2) and (other[1] <= self.y2))

    def width(self):
        return self.x2 - self.x1

    def height(self):
        return self.y2 - self.y1

    def left(self):
        return self.x1

    def right(self):
        return self.x2

    def top(self):
        return self.y1

    def bottom(self):
        return self.y2

    def upperLeft(self):
        return Vector(self.x1, self.y1)

    def lowerRight(self):
        return Vector(self.x2, self.y2)

    def center(self):
        return Vector((self.x2 + self.x1) / 2,
                      (self.y2 + self.y1) / 2)

    def size(self):
        return Vector(self.width(), self.height())

    def empty(self):
        return self._empty

    def __mul__(self, factor):
        return Rect(*map(lambda x: x * factor, self))

    def addBorder(self, w, h=None):
        if h is None:
            h = w
        self.x1 -= w
        self.y1 -= h
        self.x2 += w
        self.y2 += h

    def __repr__(self):
        return "fig.Rect(%d,%d,%d,%d)" % (self.x1, self.y1, self.x2, self.y2)

    def __str__(self):
        return "%d,%d-%d,%d" % (self.x1, self.y1, self.x2, self.y2)

    def __eq__(self, other):
        if not isinstance(other, Rect):
            return False
        return str(self) == str(other)

    def __ne__(self, other):
        if isinstance(other, Rect):
            return False
        return str(self) != str(other)

    def __iter__(self):
        """Make Rect objects assignable like::
        x1, y1, x2, y2 = someRect"""
        yield self.x1
        yield self.y1
        yield self.x2
        yield self.y2


# --------------------------------------------------------------------
# 							custom colors
# --------------------------------------------------------------------

class CustomColor(object):
    def __init__(self, index, hexCode):
        assert len(hexCode) == 7 and hexCode.startswith("#"), \
            "invalid hexCode given to CustomColor(), should look like '#fe0d00'"
        self.index = index
        self.hexCode = hexCode

    # sys.stderr.write("CustomColor(%d, '%s') -> %s" % (index, hexCode, repr(self)))

    def __repr__(self):
        return _join(ObjectType.CustomColor, self.index, self.hexCode) + "\n"

    def __str__(self):
        return str(self.index)

    def __int__(self):
        return self.index

    def __cmp__(self, other):
        if other == None:
            return 1
        if isinstance(other, CustomColor):
            return cmp(self.index, other.index)
        if isinstance(other, str):
            return cmp(self.hexCode, other)
        return cmp(self.index, other)

    def __sub__(self, other):
        """Return RGB vector difference as (dr,dg,db) tuple."""
        return map(operator.sub, self, other)

    def __getitem__(self, index):
        if index > 2:
            raise IndexError("CustomColor.__getitem__: Only three components (r,g,b)!")
        return int(self.hexCode[2 * index + 1:2 * index + 3], 16)

    def __len__(self):
        return 3

    def rgb(self):
        return (self[0], self[1], self[2])

    def setRGB(self, r, g, b):
        self.hexCode = "#%02x%02x%02x" % (r, g, b)


# --------------------------------------------------------------------
# 				Object: base class for all fig objects
# --------------------------------------------------------------------

class Object(object):
    """Base class of all fig objects.  Handles common properties like

    - lineStyle (see `LineStyle.XXX` constants)
    - lineWidth (1/80th inch)
    - styleValue (dash length / dot gap ratio), in 1/80th inches
    - penColor, fillColor (see `Color.XXX` constants)
    - fillStyle (see `FillStyle.XXX` constants)
    - depth (0-999)
    - joinStyle (see `JoinStyle.XXX` constants)
    - capStyle (see `CapStyle.XXX` constants)
    - forwardArrow/backwardArrow (`Arrow` objects)"""

    __slots__ = ("lineStyle", "lineWidth", "penColor", "fillColor", "depth",
                 "penStyle", "fillStyle", "styleValue", "joinStyle", "capStyle",
                 "forwardArrow", "backwardArrow", "comment")

    def __init__(self):
        self.lineStyle = LineStyle.Default
        # Line thicknesses are given in 1/80 inch (0.3175mm) or 1 screen pixel.
        # When exporting to EPS, PostScript or any bitmap format (e.g. GIF),  the
        # line thickness is reduced to 1/160 inch (0.159mm) to "lighten" the look.
        self.lineWidth = 1
        self.penColor = Color.Default
        self.fillColor = Color.Default
        self.depth = 50
        self.penStyle = 0  # not used
        self.fillStyle = FillStyle.None_
        self.styleValue = 3.0
        self.joinStyle = JoinStyle(0)
        self.capStyle = CapStyle(0)
        self.forwardArrow = None
        self.backwardArrow = None
        self.comment = ""

    def _joinWithProperties(self, figType, subType, *rest):
        return _formatComment(self.comment) + _join(
            figType, subType,
            self.lineStyle, self.lineWidth,
            self.penColor is None and Color.Default or self.penColor,
            self.fillColor is None and Color.Default or self.fillColor,
            self.depth, self.penStyle,
            self.fillStyle, str(self.styleValue),
            *rest)


class Arrow(object):
    """Arrow objects store arrow parameters of open arcs, splines, or
    lines.  Instances of this class are usually assigned to the
    `forwardArrow`/`backwardArrow` properties of `fig.Object`.
    The Arrow properties are

    - type (see `ArrowType.XXX` constants)
    - style (`ArrowStyle.Hollow` or `ArrowStyle.Filled`)
    - thickness, in 1/80th inches
    - width, height (in fig units)"""

    __slots__ = ("type", "style", "thickness", "width", "height")

    def __init__(self, type=ArrowType.Stick, style=ArrowStyle.Hollow,
                 thickness=1.0, width=60.0, height=120.0):
        self.type = type
        self.style = style
        self.thickness = thickness
        self.width = width
        self.height = height

    def __str__(self):
        return _join(self.type, self.style,
                     str(self.thickness),
                     str(self.width), str(self.height)) + "\n"


def readArrow(params):
    return Arrow(int(params[0]), int(params[1]),
                 float(params[2]), float(params[3]), float(params[4]))


# --------------------------------------------------------------------
#                                arcs
# --------------------------------------------------------------------

class ArcBase(Object):
    """Base class of Arc-like objects (`PieArc`, `OpenArc`)."""

    __slots__ = ("points", "direction", "center", "_pointCount")

    def __init__(self, center=None,
                 point1=None, point2=None,
                 angle1=None, angle2=None, radius=None,
                 direction=ArcDirection.Clockwise):
        Object.__init__(self)
        self.center = center
        self.points = None
        self.direction = direction
        if center == None:
            assert point1 == None and point2 == None
            return
        assert ((point1 is None) == (point2 is None)) and \
               ((angle1 is None) == (angle2 is None) == (radius is None)) and \
               ((point1 is None) != (angle1 is None)), \
            "ArcBase.__init__: give either points *or* angles+radius!"

        if not angle1 is None:
            point1 = center + (radius * math.cos(angle1), -radius * math.sin(angle1))
            point2 = center + (radius * math.cos(angle2), -radius * math.sin(angle2))

        # calculate midpoint between start- and end-point on arc
        self.points = [point1, None, point2]
        angle1, angle2 = self.angles()
        angle12 = angle1 + self._angleDiff(angle2, angle1, direction) / 2
        c = Vector(*center)
        self.points[1] = \
            c + (c - point1).length() * Vector(math.cos(angle12),
                                               -math.sin(angle12))

    def _angleDiff(self, angle2, angle1, direction):
        """Return (angle2 - angle1) in the range [-2pi..0) if
        direction == ArcDirection.Clockwise, and in the range [0..2pi) otherwise."""
        result = angle2 - angle1
        if direction == ArcDirection.Clockwise:
            while result > 0:
                result -= 2 * math.pi
            if result <= -2 * math.pi:
                result += 2 * math.pi
        else:
            while result < 0:
                result += 2 * math.pi
            if result > 2 * math.pi:
                result -= 2 * math.pi
        return result

    def angles(self):
        """Return start- and end-angle (in radians).  The second angle
        is smaller than the first iff direction is ArcDirection.Clockwise."""
        point1, _, point2 = self.points
        angle1 = math.atan2(-(point1[1] - self.center[1]),
                            point1[0] - self.center[0])
        angle2 = math.atan2(-(point2[1] - self.center[1]),
                            point2[0] - self.center[0])
        angle2 = angle1 + self._angleDiff(angle2, angle1, self.direction)
        return angle1, angle2

    def radius(self):
        """Return distance of first point from center"""
        return (Vector(*self.center) - self.points[0]).length()

    def changeType(self, arcType):
        "Change type of this Arc. arcType may be one of ArcType.Pie or ArcType.Open"
        if arcType == ArcType.Pie:
            self.__class__ = PieArc
        else:
            self.__class__ = OpenArc

    def __str__(self):
        assert len(self.points) == 3
        hasForwardArrow = (self.forwardArrow != None and 1 or 0)
        hasBackwardArrow = (self.backwardArrow != None and 1 or 0)

        result = self._joinWithProperties(
            ObjectType.Arc, self.arcType(),
            self.capStyle, self.direction,
            hasForwardArrow, hasBackwardArrow,
            str(self.center[0]), str(self.center[1]),
            self.points[0][0], self.points[0][1],
            self.points[1][0], self.points[1][1],
            self.points[2][0], self.points[2][1]) + "\n"

        if hasForwardArrow:
            result += "\t" + str(self.forwardArrow)
        if hasBackwardArrow:
            result += "\t" + str(self.backwardArrow)
        return result

    def bounds(self):
        result = Rect()
        for point in self.points:
            result(point)
        return result

    def _readSub(self, params):
        if self.forwardArrow == True:
            self.forwardArrow = readArrow(params)
            return self.backwardArrow == True

        if self.backwardArrow == True:
            self.backwardArrow = readArrow(params)
            return False

        sys.stderr.write("Unhandled subline while loading arc object!\n")
        return False


class PieArc(ArcBase):
    """Represents a closed arc object."""

    __slots__ = ()

    def arcType(self):
        "Return type of this Arc (ArcType.Pie), see `changeType`."
        return ArcType.Pie

    def closed(self):
        """Return whether this arc is closed (True for all
        `PieArc` objects.)"""
        return True


class OpenArc(ArcBase):
    """Represents an open arc object."""

    __slots__ = ()

    def arcType(self):
        "Return type of this Arc (ArcType.Open), see `changeType`."
        return ArcType.Open

    def closed(self):
        """Return whether this arc is closed (False for all
        `OpenArc` objects.)"""
        return False


def _readArcBase(params):
    result = ArcBase()
    result.changeType(int(params[0]))
    result.lineStyle = LineStyle.read(params[1])
    result.lineWidth = int(params[2])
    result.penColor = Color.read(params[3])
    result.fillColor = Color.read(params[4])
    result.depth = int(params[5])
    result.penStyle = int(params[6])
    result.fillStyle = FillStyle.read(params[7])
    result.styleValue = float(params[8])
    result.capStyle = CapStyle.read(params[9])
    result.direction = int(params[10])
    subLines = 0
    if int(params[11]):
        result.forwardArrow = True
        subLines += 1
    if int(params[12]):
        result.backwardArrow = True
        subLines += 1
    result.center = (float(params[13]), float(params[14]))
    result.points = [Vector(int(params[15]), int(params[16])),
                     Vector(int(params[17]), int(params[18])),
                     Vector(int(params[19]), int(params[20]))]
    return result, subLines


# --------------------------------------------------------------------
#                              ellipses
# --------------------------------------------------------------------

class EllipseBase(Object):
    """Base class of Ellipse-like objects (`Ellipse`, `Circle`)."""

    __slots__ = ("angle", "center", "radius", "start", "end")

    def __init__(self):
        Object.__init__(self)
        self.angle = 0.0
        self.center = Vector(0, 0)
        self.radius = Vector(0, 0)
        self.start = Vector(0, 0)
        self.end = Vector(0, 0)

    def changeType(self, ellipseType):
        """Change type of this Ellipse object.  `ellipseType` may be one
        of the `EllipseType.XXX` constants:

        - EllipseType.EllipseRadii
        - EllipseType.EllipseDiameter
        - EllipseType.CircleRadius
        - EllipseType.CircleDiameter

        This method may change the type of this object to another
        `EllipseBase`-derived class."""

        if ellipseType in (EllipseType.EllipseRadii, EllipseType.EllipseDiameter):
            self.__class__ = Ellipse
        elif ellipseType in (EllipseType.CircleRadius, EllipseType.CircleDiameter):
            self.__class__ = Circle
        else:
            raise ValueError("Unknown ellipseType %d!" % ellipseType)

    def __str__(self):
        return self._joinWithProperties(
            ObjectType.Ellipse, self.ellipseType(),
            1,  # "1" is self.direction
            str(self.angle % (2 * math.pi)),
            self.center[0], self.center[1],
            self.radius[0], self.radius[1],
            self.start[0], self.start[1],
            self.end[0], self.end[1]) + "\n"

    def bounds(self):
        result = Rect()
        result(((self.center[0] - self.radius[0]),
                (self.center[1] - self.radius[1])))
        result(((self.center[0] + self.radius[0]),
                (self.center[1] + self.radius[1])))
        return result

    def setRadius(self, radius):
        """Change radius.  `radius` may be either a tuple of x/y
        radii, or a single radius, convertible to float(s)."""
        if not isinstance(radius, tuple):
            assert float(
                radius) != None, "radius must be either a tuple of x/y radii, or a single radius, convertible to float(s)"
            self.radius = (radius, radius)
        else:
            assert len(radius) == 2 and float(radius[0]) != None and float(radius[
                                                                               1]) != None, "radius must be either a tuple of x/y radii, or a single radius, convertible to float(s)"
            self.radius = radius
        # FIXME: depend on ellipseType (currently, ellipseType may change)
        self.start = self.center
        self.end = (self.center[0] + self.radius[0],
                    self.center[1] + self.radius[1])

    def setCenterRadius(self, center, radius):
        """Set center and radius, see `setRadius`."""
        self.center = center
        self.setRadius(radius)


def _readEllipseBase(params):
    result = EllipseBase()
    result.changeType(int(params[0]))
    result.lineStyle = LineStyle.read(params[1])
    result.lineWidth = int(params[2])
    result.penColor = Color.read(params[3])
    result.fillColor = Color.read(params[4])
    result.depth = int(params[5])
    result.penStyle = int(params[6])
    result.fillStyle = FillStyle.read(params[7])
    result.styleValue = float(params[8])
    result.angle = float(params[10])
    result.center = Vector(int(params[11]), int(params[12]))
    result.radius = Vector(int(params[13]), int(params[14]))
    result.start = Vector(int(params[15]), int(params[16]))
    result.end = Vector(int(params[17]), int(params[18]))
    return result, 0


class Ellipse(EllipseBase):
    """Represents an ellipse object.  Ellipse objects have an
    attribute `radius` that is a tuple of two radii in x- and
    y-direction."""

    __slots__ = ()

    def __init__(self, center=None, radii=None, angle=0.0,
                 start=None, end=None):
        EllipseBase.__init__(self)
        self.angle = angle
        if center != None and radii != None:
            self.setCenterRadius(center, radii)
        else:
            self.setStartEnd(start, end)

    def ellipseType(self):
        """Return type of this ellipse (one of EllipseType.EllipseRadii,
        EllipseType.EllipseDiameter for `Ellipse` objects), see `changeType`."""

        if self.center == self.start:
            return EllipseType.EllipseRadii
        else:
            return EllipseType.EllipseDiameter

    def setStartEnd(self, start, end):
        self.start = start
        self.end = end
        # FIXME: depend on ellipseType
        self.center = ((start[0] + end[0]) / 2,
                       (start[1] + end[1]) / 2)
        self.radius = ((end[0] - self.center[0]),
                       (end[1] - self.center[1]))


class Circle(EllipseBase):
    """Represents a circle object.  Circle objects have an
    attribute `radius` that is a single float."""

    __slots__ = ()

    def __init__(self, center=None, radius=None,
                 start=None, end=None):
        EllipseBase.__init__(self)
        if center != None and radius != None:
            self.setCenterRadius(center, (radius, radius))
        else:
            self.setStartEnd(start, end)

    def ellipseType(self):
        """Return type of this ellipse (one of EllipseType.CircleRadius,
        EllipseType.CircleDiameter for `Circle` objects), see `changeType`."""

        if self.center == self.start:
            return EllipseType.CircleRadius
        else:
            return EllipseType.CircleDiameter

    def setStartEnd(self, start, end):
        self.start = start
        self.end = end
        # FIXME: depend on ellipseType?
        self.center = ((start[0] + end[0]) / 2,
                       (start[1] + end[1]) / 2)
        radius = math.hypot(end[0] - self.center[0],
                            end[1] - self.center[1])
        self.radius = (radius, radius)

    def __str__(self):
        assert self.radius[0] == self.radius[1], \
            "invalid circle (radii %s != %s)" % self.radius
        return EllipseBase.__str__(self)


# --------------------------------------------------------------------
#                             polylines
# --------------------------------------------------------------------

class PolylineBase(Object):
    """Base class of Polygon-like objects (`Polygon`,
    `Polyline`, `PictureBBox`)."""

    __slots__ = ("points", "filename", "flipped", "radius", "_pointCount")

    def __init__(self):
        Object.__init__(self)
        self.points = []
        self.filename = None
        self.flipped = False
        self.radius = -1

    def changeType(self, polylineType, retainPoints=False):
        """Change type of this Polyline object.  `polylineType` may be one
        of the `PolygonType.XXX` constants:

        - PolygonType.Polyline
        - PolygonType.Box
        - PolygonType.Polygon
        - PolygonType.ArcBox
        - PolygonType.PictureBBox

        This method may change the type of this object to another
        `PolylineBase`-derived class.

        If `retainPoints` is not set to True, this function will
        add/remove the last point such that closed polygons do not
        have the first point repeated at the end."""

        wasClosed = None
        if type(self) != PolylineBase:
            wasClosed = self.closed()
        if polylineType == PolygonType.Polyline:
            self.__class__ = Polyline
        if polylineType == PolygonType.Box:
            self.__class__ = PolyBox
        if polylineType == PolygonType.Polygon:
            self.__class__ = Polygon
        if polylineType == PolygonType.ArcBox:
            self.__class__ = ArcBox
        if polylineType == PolygonType.PictureBBox:
            self.__class__ = PictureBBox
        if retainPoints or wasClosed == None:
            return
        if wasClosed == self.closed() or len(self.points) < 2:
            return
        if not wasClosed:
            if self.points[-1] == self.points[0]:
                del self.points[-1]
        else:
            self.points.append(copy.copy(self.points[0]))

    def segments(self):
        it = iter(self.points)
        prev = it.next()
        for point in it:
            yield (prev, point)
            prev = point
        if self.closed():
            yield (prev, self.points[0])

    def __str__(self):
        pointCount = len(self.points)
        if self.closed():
            pointCount += 1
        hasForwardArrow = (self.forwardArrow != None and 1 or 0)
        hasBackwardArrow = (self.backwardArrow != None and 1 or 0)

        result = self._joinWithProperties(
            ObjectType.Polygon, self.polylineType(),
            self.joinStyle, self.capStyle, self.radius,
            hasForwardArrow, hasBackwardArrow,
            pointCount) + "\n"

        if hasForwardArrow:
            result += "\t" + str(self.forwardArrow)
        if hasBackwardArrow:
            result += "\t" + str(self.backwardArrow)
        if isinstance(self, PictureBBox):
            result += "\t" + _join(self.flipped, self.filename) + "\n"
        i = self._savePointIter()
        for linePoints in map(None, *(i,) * 12):
            result += "\t" + _join(*[p for p in linePoints if p != None]) + "\n"
        return result

    def _savePointIter(self):
        for p in self.points:
            yield p[0]
            yield p[1]
        if self.closed():
            yield self.points[0][0]
            yield self.points[0][1]

    def bounds(self):
        result = Rect()
        for point in self.points:
            result(point)
        return result

    def _readSub(self, params):
        if self.forwardArrow == True:
            self.forwardArrow = readArrow(params)
            return True

        if self.backwardArrow == True:
            self.backwardArrow = readArrow(params)
            return True

        if isinstance(self, PictureBBox) and self.filename == None:
            self.flipped = int(params[0])
            self.filename = params[1]
            return True

        pointCount = len(params) / 2
        for pointIndex in range(pointCount):
            self.points.append(Vector(int(params[pointIndex * 2]),
                                      int(params[pointIndex * 2 + 1])))

        expectedPoints = (self._pointCount + (self.closed() and 1 or 0))
        moreToCome = len(self.points) < expectedPoints
        if len(self.points) > self._pointCount:
            if len(self.points) > expectedPoints:
                sys.stderr.write("WARNING: read too many points?!\n")
            del self.points[self._pointCount:]

        return moreToCome


def _readPolylineBase(params):
    result = PolylineBase()
    # retainPoints is not actually necessary for PolylineBase objects:
    result.changeType(int(params[0]), retainPoints=True)
    result.lineStyle = LineStyle.read(params[1])
    result.lineWidth = int(params[2])
    result.penColor = Color.read(params[3])
    result.fillColor = Color.read(params[4])
    result.depth = int(params[5])
    result.penStyle = int(params[6])
    result.fillStyle = FillStyle.read(params[7])
    result.styleValue = float(params[8])
    result.joinStyle = JoinStyle.read(params[9])
    result.capStyle = CapStyle.read(params[10])
    result.radius = int(params[11])
    subLines = 0
    if int(params[12]):
        result.forwardArrow = True
        subLines += 1
    if int(params[13]):
        result.backwardArrow = True
        subLines += 1
    result._pointCount = int(params[14])
    subLines += (result._pointCount + 5) / 6  # sublines to read for the points
    if result.closed():
        result._pointCount -= 1
    if isinstance(result, PictureBBox):
        subLines += 1
    return result, subLines


class PolyBox(PolylineBase):
    """Represents a rectangular closed box object."""

    __slots__ = ()

    def __init__(self, x1, y1, x2, y2):
        PolylineBase.__init__(self)
        self.points.append(Vector(x1, y1))
        self.points.append(Vector(x2, y1))
        self.points.append(Vector(x2, y2))
        self.points.append(Vector(x1, y2))

    def polylineType(self):
        """Return type of this polygon (PolygonType.Box for all `PolyBox` objects),
        see `changeType`."""

        return PolygonType.Box

    def closed(self):
        """Return whether this polygon is closed (True for all
        `PolyBox` objects.)"""
        return True

    def center(self):
        """Return (x, y) coordinate tuple of the midpoint of this box."""
        return ((self.points[0][0] + self.points[2][0]) / 2,
                (self.points[0][1] + self.points[2][1]) / 2)

    def upperLeft(self):
        """Return coordinates of upper left corner."""
        return self.points[0]

    def lowerRight(self):
        """Return coordinates of lower right corner."""
        return self.points[2]

    def width(self):
        """Return width of this box."""
        return abs(self.points[2][0] - self.points[0][0])

    def height(self):
        """Return height of this box."""
        return abs(self.points[2][1] - self.points[0][1])


class ArcBox(PolyBox):
    """Represents a rectangular box with rounded corners."""

    __slots__ = ()

    def polylineType(self):
        """Return type of this polygon (PolygonType.ArcBox for all `ArcBox` objects),
        see `changeType`."""

        return PolygonType.ArcBox


class Polygon(PolylineBase):
    """Represents a closed polygon object."""

    __slots__ = ()

    def __init__(self, points, closed=True):
        PolylineBase.__init__(self)
        self.points = points
        if not closed:
            self.changeType(PolygonType.Polyline, retainPoints=True)

    def polylineType(self):
        """Return type of this polygon (PolygonType.Polygon for all `Polygon` objects),
        see `changeType`."""

        return PolygonType.Polygon

    def closed(self):
        """Return whether this polygon is closed (True for all
        `Polygon` objects.)"""
        return True


class Polyline(PolylineBase):
    """Represents an open polygon object."""

    __slots__ = ()

    def __init__(self, points):
        PolylineBase.__init__(self)
        self.points = points

    def polylineType(self):
        """Return type of this polygon (PolygonType.Polyline for all `Polyline`
        objects), see `changeType`."""

        return PolygonType.Polyline

    def closed(self):
        """Return whether this polygon is closed (False for all
        `Polygon` objects.)"""

        return False


class PictureBBox(PolyBox):
    """Represents a picture embedded in an XFig file.  The filename is
    stored in the `filename` attribute."""

    __slots__ = ()

    def __init__(self, x1, y1, x2, y2, filename, flipped=False):
        PolyBox.__init__(self, x1, y1, x2, y2)
        self.filename = filename
        self.flipped = flipped

    def polylineType(self):
        """Return type of this polygon (PolygonType.PictureBBox for all
        `PictureBBox` objects), see `changeType`."""

        return PolygonType.PictureBBox

    def closed(self):
        """Return whether this polygon is closed (True for all
        `PictureBBox` objects.)"""
        return True


# --------------------------------------------------------------------
#                              splines
# --------------------------------------------------------------------

class SplineBase(Object):
    """Base class of Spline objects (`ApproximatedSpline`,
    `InterpolatedSpline`, `XSpline`)."""

    __slots__ = ("points", "_shapeFactors", "_closed", "_pointCount")

    def __init__(self, points=None, shapeFactors=None, closed=True):
        Object.__init__(self)
        self.points = points or []
        self._shapeFactors = shapeFactors or []
        self._closed = closed

    def closed(self):
        """Return whether this spline curve is closed."""
        assert self._closed != None, "SplineBase.closed(): _closed not initialized!"
        return self._closed

    def shapeFactors(self):
        """Return shape factors.  The return value is fixed for
        non-XSplines.  For XSplines, self._shapeFactors is used (no
        public API ATM)."""
        result = self._shapeFactors
        if not len(result):  # or self.defaultShapeFactor():
            # create default shapeFactors if not initialized
            result = [self.defaultShapeFactor()] * len(self.points)
            if not self.closed():
                result[0] = 0.0
                result[-1] = 0.0
        return result

    def changeType(self, splineType):
        """Change type of this Spline object.  `splineType` may be one
        of the `SplineType.XXX` constants:

        - SplineType.OpenApproximated
        - SplineType.ClosedApproximated
        - SplineType.OpenInterpolated
        - SplineType.ClosedInterpolated
        - SplineType.OpenXSpline
        - SplineType.ClosedXSpline

        This method may change the type of this object to another
        `SplineBase`-derived class."""

        if splineType == SplineType.OpenApproximated:
            self.__class__ = ApproximatedSpline
            self._closed = False
        elif splineType == SplineType.ClosedApproximated:
            self.__class__ = ApproximatedSpline
            self._closed = True
        elif splineType == SplineType.OpenInterpolated:
            self.__class__ = InterpolatedSpline
            self._closed = False
        elif splineType == SplineType.ClosedInterpolated:
            self.__class__ = InterpolatedSpline
            self._closed = True
        elif splineType == SplineType.OpenXSpline:
            self.__class__ = XSpline
            self._closed = False
        elif splineType == SplineType.ClosedXSpline:
            self.__class__ = XSpline
            self._closed = True

    def __str__(self):
        pointCount = len(self.points)

        hasForwardArrow = (self.forwardArrow != None and 1 or 0)
        hasBackwardArrow = (self.backwardArrow != None and 1 or 0)

        result = self._joinWithProperties(
            ObjectType.Spline, self.splineType(),
            self.capStyle,
            hasForwardArrow, hasBackwardArrow,
            pointCount) + "\n"

        if hasForwardArrow:
            result += "\t" + str(self.forwardArrow)
        if hasBackwardArrow:
            result += "\t" + str(self.backwardArrow)

        i = self._savePointIter()
        for linePoints in map(None, *(i,) * 12):
            result += "\t" + _join(*[p for p in linePoints if p != None]) + "\n"

        i = iter(self.shapeFactors())
        for lineSF in map(None, *(i,) * 8):
            result += "\t" + _join(*[str(sf) for sf in lineSF if sf != None]) + "\n"

        return result

    def _savePointIter(self):
        for p in self.points:
            yield p[0]
            yield p[1]

    def bounds(self):
        """Return the bounds of this object.  This is not accurate at
        all, since it simply returns the bounding box of the support
        points, but the curve may well run outside of that box."""
        # FIXME
        result = Rect()
        for point in self.points:
            result(point)
        return result

    def _readSub(self, params):
        if self.forwardArrow == True:
            self.forwardArrow = readArrow(params)
            return True

        if self.backwardArrow == True:
            self.backwardArrow = readArrow(params)
            return True

        expectedPoints = self._pointCount

        if len(self.points) < expectedPoints:
            pointCount = len(params) / 2
            for pointIndex in range(pointCount):
                self.points.append(Vector(int(params[pointIndex * 2]),
                                          int(params[pointIndex * 2 + 1])))
            if len(self.points) > expectedPoints:
                sys.stderr.write("WARNING: read too many points?!\n")
                del self.points[expectedPoints:]
            return True

        if len(self._shapeFactors) < expectedPoints:
            sfCount = len(params)
            for sfIndex in range(sfCount):
                self._shapeFactors.append(float(params[sfIndex]))
            moreToCome = len(self._shapeFactors) < expectedPoints
            if len(self._shapeFactors) > expectedPoints:
                sys.stderr.write("WARNING: read too many shapeFactors?!\n")
                del self._shapeFactors[expectedPoints:]
            if moreToCome:
                return True

        return False


class ApproximatedSpline(SplineBase):
    """Represents an open or closed approximated spline object."""

    __slots__ = ()

    def defaultShapeFactor(self):
        return 1.0

    def splineType(self):
        return self._closed and SplineType.ClosedApproximated or SplineType.OpenApproximated


class InterpolatedSpline(SplineBase):
    """Represents an open or closed interpolated spline object."""

    __slots__ = ()

    def defaultShapeFactor(self):
        return -1.0

    def splineType(self):
        return self._closed and SplineType.ClosedInterpolated or SplineType.OpenInterpolated


class XSpline(SplineBase):
    """Represents an open or closed 'x-spline' object."""

    __slots__ = ()

    def defaultShapeFactor(self):
        return 0.0  # ATT: this value is checked in shapeFactors() ATM

    def splineType(self):
        return self._closed and SplineType.ClosedXSpline or SplineType.OpenXSpline


def _readSplineBase(params):
    result = SplineBase()
    result.changeType(int(params[0]))
    result.lineStyle = LineStyle.read(params[1])
    result.lineWidth = int(params[2])
    result.penColor = Color.read(params[3])
    result.fillColor = Color.read(params[4])
    result.depth = int(params[5])
    result.penStyle = int(params[6])
    result.fillStyle = FillStyle.read(params[7])
    result.styleValue = float(params[8])
    result.capStyle = CapStyle.read(params[9])
    subLines = 0
    if int(params[10]):
        result.forwardArrow = True
        subLines += 1
    if int(params[11]):
        result.backwardArrow = True
        subLines += 1
    result._pointCount = int(params[12])
    subLines += (result._pointCount + 5) / 6  # sublines to read for the points
    return result, subLines


# --------------------------------------------------------------------
#                            text objects
# --------------------------------------------------------------------

class Text(Object):
    """Represents a text object.  Text instances have a number of
    extra attributes:

    - text (the string)
    - x, y (position)
    - alignment (cf. `Alignment.XXX` constants)
    - font (cf. Font.XXX constants)
    - fontSize (default: 12)
    - fontFlags (cf. `FontFlag.XXX` constants, default: FontFlag.PostScript)
    - angle (default: 0.0)
    - length, height (dummy values, no guarantee about correctness)
    """

    __slots__ = ("text", "pos", "alignment",
                 "font", "fontSize", "fontFlags", "angle",
                 "length", "height")

    def __init__(self, pos, text,
                 font=None, fontSize=12, fontFlags=FontFlag.PostScript,
                 alignment=Alignment.Left, angle=0.0):
        Object.__init__(self)
        self.pos = pos
        self.text = text
        self.font = font
        self.fontSize = fontSize
        self.fontFlags = fontFlags
        self.alignment = alignment
        self.angle = angle
        self.height = 136
        self.length = 100  # dummy value

    def _guessHeight(self):
        """Guessed height of font in fig units."""
        return self.fontSize * 34 / 3

    def _length(self):
        """FIXME: If this is corrected, remove underscore prefix."""
        return 100

    def bounds(self):
        result = Rect()
        if self.alignment == Alignment.Left:
            result((self.pos[0], self.pos[1] - self.height))
            result((self.pos[0] + self.length, self.pos[1]))
        elif self.alignment == Alignment.Centered:
            result((self.pos[0] - self.length / 2, self.pos[1] - self.height))
            result((self.pos[0] + self.length / 2, self.pos[1]))
        elif self.alignment == Alignment.Right:
            result((self.pos[0], self.pos[1] - self.height))
            result((self.pos[0] + self.length, self.pos[1]))
        return result

    # def __str__(self):
    #     font = self.font
    #     if self.font is None:
    #         font = self.fontFlags & FontFlag.PostScript \
    #                and fontDefault or LaTeXFont.Default
    #     result = _formatComment(self.comment) + \
    #              _join(ObjectType.Text, self.alignment,
    #                    self.penColor is None and Color.Default or self.penColor,
    #                    self.depth, self.penStyle,
    #                    font, self.fontSize, str(self.angle), self.fontFlags,
    #                    self.height, self.length, self.pos[0], self.pos[1],
    #                    _escapeText(self.text + "\x01")) + "\n"
    #
    #     return result

    def __repr__(self):
        return "<fig.Text at %s, '%s'>" % ((self.pos[0], self.pos[1]), self.text)


def _escapeText(text):
    nonPrintable = re.compile("[\x00-\x08\x0e-\x1f\x80-\xff]")
    return nonPrintable.sub(lambda ma: "\\%03o" % ord(ma.string[ma.start()]),
                            text.replace("\\", "\\\\"))


def _unescapeText(text):
    chunks = text.split("\\")
    result = chunks[0]
    i = 1
    while i < len(chunks):
        if chunks[i]:
            result += chr(int(chunks[i][:3], 8)) + chunks[i][3:]
            i += 1
        else:
            result += "\\" + chunks[i + 1]
            i += 2
    return result


def _readText(params, text):
    result = Text(Vector(int(params[10]), int(params[11])), _unescapeText(text),
                  alignment=int(params[0]))
    result.penColor = Color.read(params[1])
    result.depth = int(params[2])
    result.penStyle = int(params[3])
    result.font = Font.read(params[4])
    result.fontSize = float(params[5])
    result.angle = float(params[6])
    result.fontFlags = int(params[7])
    # print float(params[8])/result.fontSize, float(params[9])/len(result.text)
    result.height = float(params[8])
    result.length = float(params[9])
    return result, 0


# --------------------------------------------------------------------
#              Container and ObjectProxy utility classes
# --------------------------------------------------------------------

class _AllObjectIter(object):
    "helper class, see `Container.allObjects`"

    def __init__(self, container, includeCompounds):
        self.file = file
        self.iters = [iter(container)]
        self.includeCompounds = includeCompounds

    def __iter__(self):
        return self

    def next(self):
        if not self.iters:
            raise StopIteration
        try:
            next = self.iters[-1].next()
            if isinstance(next, Compound):
                self.iters.append(iter(next))
                if self.includeCompounds:
                    return next
            else:
                return next
        except StopIteration:
            del self.iters[-1]
        return self.next()


class Container(list):
    """Container for fig objects, derived from the standard python
    list.  This is the common superclass of `File` (for the whole
    document), `Compound`, and `ObjectProxy` (for search results, see
    `findObjects()` or `layer()`)."""

    __slots__ = ()

    def allObjects(self, includeCompounds=False):
        """container.allObjects(includeCompounds = False) -> iterator

        Returns an iterator iterating over all objects in this
        container, recursively entering compound objects.  You can use
        the optional parameter includeCompounds (default: False) to
        get the compound objects themselves returned, too."""

        return _AllObjectIter(self, includeCompounds)

    def findObjects(self, **kwargs):
        """Return a list of objects which have attribute/value pairs
        matching the given keyword parameters.  The key "type" is
        treated special, see these useful examples::

          figFile.findObjects(depth = 40)
          figFile.findObjects(type = fig.Polygon)
          # all conditions must be fulfilled:
          figFile.findObjects(lineWidth = 10, depth = 100)
          # for disjunctive conditions, use list concatenation:
          figFile.findObjects(depth = 10) + figFile.findObjects(depth = 20)

        The returned object is actually an `ObjectProxy`, which is a
        special `Container` (which is a special python list) and allows
        to quickly change properties on all contained objects.  See
        the `Container` and `ObjectProxy` classes."""

        result = ObjectProxy(parent=self)
        for o in self.allObjects("type" in kwargs and kwargs["type"] == Compound):
            match = True
            for key, value in kwargs.items():
                if key == "type":
                    if not isinstance(o, value):
                        match = False
                        break
                elif key == "within":
                    if not value.contains(o.bounds()):
                        match = False
                        break
                elif getattr(o, key, "attribNotPresent") != value:
                    match = False
                    break
            if match:
                result.append(o)
        return result

    def layer(self, layer):
        """container.layer(layer) -> `ObjectProxy`

        Returns an `ObjectProxy` for all objects within this container
        that have the given depth; convenience shortcut for
        ``findObjects(depth = layer)``."""

        return self.findObjects(depth=layer)

    def layers(self):
        """container.layers() -> list

        Returns the list of all integer depths that are assigned to at
        least one object within this container."""

        result = dict.fromkeys([ob.depth for ob in self.allObjects()]).keys()
        result.sort()
        return result

    def __deepcopy__(self, memo):
        result = type(self)([copy.deepcopy(o, memo) for o in self])
        return result

    def remove(self, obj):
        """container.remove(obj)

        Removes the given object from this `Container`.  Also works
        recursively for objects within `Compound` objects within this
        `Container`.  Raises a ValueError if `obj` is not
        contained."""

        try:
            list.remove(self, obj)
        except ValueError:
            for o in self:
                if isinstance(o, Compound):
                    try:
                        o.remove(obj)
                        return
                    except ValueError:
                        pass
            raise ValueError("remove(): Given object not found in Container.")

    def container(self):
        """Return self, see `ObjectProxy.container()`."""
        return self

    def bounds(self):
        """Return the union of all bounding boxes of the contained
        objects.  This value is not cached (because it cannot be
        reliably updated if childrens change) but will be determined
        on each call."""

        result = Rect()
        for object in self:
            result(object.bounds())
        return result


class ObjectProxy(Container):
    """An ObjectProxy is a special `Container` that is used for search
    results (see `Container.findObjects`) which offers additional
    features:

    remove():
      Use like ``foo.findObjects(type = fig.Polyline).remove()``

      Removes all objects within this object proxy from the parent
      container (the one `findObjects` was called on).

    setting attributes:
      ``foo.findObjects(type = fig.Polyline).lineWidth = 4``

      Setting an attribute is promoted to all contained objects which
      have that attribute.  (E.g. setting fontSize will affect only
      Text objects.)

    querying attributes:
      ``col = file.layer(50).penColor``

      Objects that do not have the attribute are gracefully skipped;
      `None` is returned if the objects do not all have the same value
      for the requested attribute.  (An `AttributeError` is only
      raised if none of the objects has the requested attribute.)"""

    __slots__ = ("parent",)

    def __init__(self, objects=[], parent=None):
        Container.__init__(self, objects)
        self.parent = parent

    def __setattr__(self, key, value):
        if key == "parent":
            Container.__setattr__(self, key, value)
            return
        for ob in self:
            if hasattr(ob, key):
                setattr(ob, key, value)

    def __getattr__(self, key):
        """Forwards attribute lookup to the contained objects.

        If the attribute has the same value for all objects, it is
        returned, otherwise (the attribute has different values among
        them), `None` is returned.

        Objects that do not have the named attribute are simply
        ignored (i.e. proxy.font will gracefully skip non-`Text`
        objects).  An `AttributeError` is only raised of none of the
        objects has the requested attribute."""

        found = False
        result = None  # (prevent false positive in pyflakes)
        for ob in self:
            if hasattr(ob, key):
                if found:
                    if getattr(ob, key) != result:
                        return None
                else:
                    result = getattr(ob, key)
                    found = True
        if not found:
            raise AttributeError("No Object within ObjectProxy has a '%s' attribute!" % key)
        return result

    def __getslice__(self, *args):
        """Support slicing, i.e. returns an ObjectProxy with the same
        parent."""
        return ObjectProxy(Container.__getslice__(self, *args),
                           self.parent)

    def remove(self, *args):
        """When no arguments are given, remove all objects from parent
        container.  Else, remove given object from this container."""

        if not args:
            parent = self.container()
            assert parent is not None, \
                "ObjectProxy.remove() needs access to the parent"
            for ob in self:
                parent.remove(ob)
        else:
            Container.remove(self, *args)

    def container(self):
        """Return first non-ObjectProxy object in the parent chain.
        This will be the object `findObjects` has originally be called
        on."""
        result = self.parent
        while isinstance(result, ObjectProxy):
            result = result.parent
        return result

    def __add__(self, other):
        """Returns the union of two search results.  (If the two
        source ObjectProxies being added together have different
        parents, the result will have a parent of None.)"""
        parent = self.container()
        if parent is not other.container():
            parent = None
        if isinstance(other, list):
            return ObjectProxy(list.__add__(self, other), parent)


# --------------------------------------------------------------------
#                             compounds
# --------------------------------------------------------------------

class Compound(Container):
    """Represents a group of XFig objects."""

    __slots__ = ("comment",)

    def __init__(self, parent=None):
        Container.__init__(self)
        self.comment = ""
        if parent != None:
            parent.append(self)

    def __deepcopy__(self, memo):
        result = Compound()
        for o in self:
            result.append(copy.deepcopy(o, memo))
        return result

    def __str__(self):
        if len(self) < 1:
            return ""
        contents = ""
        for o in self:
            contents += str(o)
        b = self.bounds()
        return _formatComment(self.comment) + \
               _join(ObjectType.CompoundBegin,
                     int(b.x1), int(b.y1),
                     int(b.x2), int(b.y2)) + "\n" + \
               contents + str(ObjectType.CompoundEnd) + "\n"


def _readCompound(params):
    # ignore bounds passed in params, since we cannot guarantee proper
    # updating later:
    return Compound()


# --------------------------------------------------------------------
#                                file
# --------------------------------------------------------------------

class File(Container):
    """Main class of the `fig` module, represents an XFig document."""

    __slots__ = ("comment", "landscape", "centered", "metric", "paperSize",
                 "magnification", "singlePage", "transparentColor", "ppi",
                 "filename", "colors", "_colorhash")

    def __init__(self, inputFile=None):
        Container.__init__(self)
        self.colors = []
        self._colorhash = {}
        self.filename = None

        if inputFile == None:
            self.comment = ""
            self.landscape = False
            self.centered = True
            self.metric = True
            self.paperSize = "A4"
            self.magnification = 100.0
            self.singlePage = True
            self.transparentColor = -2  # no transparency, -1 = background, else color#
            self.ppi = 1200  # figure units per inch
        else:
            lineIndex = 0
            extraLineCount = 0
            stack = []
            currentObject = None
            currentComment = ""
            subLineExpected = 0
            if isinstance(inputFile, str):
                self.filename = inputFile
                inputFile = file(inputFile).readlines()
            elif hasattr(inputFile, "readlines"):
                if hasattr(inputFile, "name"):
                    self.filename = inputFile.name
                inputFile = inputFile.readlines()
            # for error messages:
            filename = self.filename and "'%s'" % self.filename or "<unnamed>"
            for line in inputFile:
                if line.startswith("#"):
                    if lineIndex:
                        currentComment += line[1:]
                    extraLineCount += 1
                    continue
                line = line.strip()
                if not line:
                    extraLineCount += 1
                    continue
                # print line
                if lineIndex == 0:
                    self.landscape = (line.lower().startswith("landscape"))
                elif lineIndex == 1:
                    self.centered = (line.lower().startswith("center"))
                elif lineIndex == 2:
                    self.metric = (line.lower().startswith("metric"))
                elif lineIndex == 3:
                    self.paperSize = line
                elif lineIndex == 4:
                    self.magnification = float(line)
                elif lineIndex == 5:
                    self.singlePage = (line.lower().startswith("single"))
                elif lineIndex == 6:
                    self.transparentColor = int(line)
                elif lineIndex == 7:
                    res, sysDummy = line.split()
                    self.ppi = int(res)
                    self.comment = currentComment
                    currentComment = ""
                else:
                    try:
                        params = line.split()
                        if subLineExpected:
                            subLineExpected = currentObject._readSub(params)
                        else:
                            objectType = ObjectType(int(params[0]))
                            subLineExpected = 0
                            if objectType == ObjectType.CustomColor:
                                cc = self.addColor(CustomColor(int(params[1]), params[2]))
                                assert cc.index == Color.Custom0 + len(self.colors) - 1, \
                                    "non-contiguous custom color indices found - not handled yet!"
                            elif objectType == ObjectType.Polygon:
                                currentObject, subLineExpected = _readPolylineBase(params[1:])
                                currentObject.comment = currentComment
                                currentComment = ""
                            elif objectType == ObjectType.Arc:
                                currentObject, subLineExpected = _readArcBase(params[1:])
                                currentObject.comment = currentComment
                                currentComment = ""
                            elif objectType == ObjectType.Spline:
                                currentObject, subLineExpected = _readSplineBase(params[1:])
                                currentObject.comment = currentComment
                                currentComment = ""
                            elif objectType == ObjectType.Text:
                                assert line[-4:] == "\\001"
                                currentObject, subLineExpected = _readText(
                                    params[1:], (
                                                    line.split(None, 12)[-1]).split(" ", 1)[1][:-4])
                                currentObject.comment = currentComment
                                currentComment = ""
                            elif objectType == ObjectType.Ellipse:
                                currentObject, subLineExpected = _readEllipseBase(params[1:])
                                currentObject.comment = currentComment
                                currentComment = ""
                            elif objectType == ObjectType.CompoundBegin:
                                stack.append(_readCompound(params[1:]))
                                stack[-1].comment = currentComment
                                currentComment = ""
                            elif objectType == ObjectType.CompoundEnd:
                                currentObject = stack.pop()
                            else:
                                raise ValueError(
                                    "Unhandled object type %s!" % (objectType,))
                        if currentObject != None and not subLineExpected:
                            if stack:
                                stack[-1].append(currentObject)
                            else:
                                self.append(currentObject)
                            currentObject = None
                    except ValueError:
                        sys.stderr.write("Parse error in %s, line %i:\n%s\n\n" %
                                         (filename, lineIndex + extraLineCount + 1, line))
                        raise
                lineIndex += 1
            assert lineIndex > 7, ".fig File truncated (header incomplete)"
            if not self:
                sys.stderr.write("WARNING: File empty (no objects read)!\n")

    def append(self, object):
        """Adds the object to this document.  `object` is supposed to
        be a `fig.Object`-derived object.  `CustomColor` objects are
        appended to self.colors as if `addColor()` was called."""

        if isinstance(object, CustomColor):
            self.addColor(object)
        else:
            Container.append(self, object)

    def addColor(self, hexCode):
        """Adds a custom color to this document.  hexCode may be
        either a hex code like #ffee00 or a CustomColor instance.
        Returns the new `CustomColor` object.
        See `getColor`, too."""

        assert len(self.colors) < 512, \
            ".fig file format does not allow more than 512 custom colors!"
        if isinstance(hexCode, str):
            result = CustomColor(Color.Custom0 + len(self.colors), hexCode)
        elif isinstance(hexCode, CustomColor):
            result = hexCode
            hexCode = result.hexCode
        else:
            raise TypeError("addColor() should be called with a hexCode (e.g. #ffee00) or a CustomColor instance")
        self.colors.append(result)
        self._colorhash[hexCode] = result
        return result

    def getColor(self, color, similarity=None):
        """Return a color object for the given color, adding a new
        custom color to this document if it does not yet exist.  The
        color can be given as tuple of R,G,B values or as hex string
        (e.g. (0, 255, 0) or '#00ff00' for green).  The range of valid
        R,G,B values depends on the type: integer values are expected
        to be in the range 0..255, while float values are interpreted
        as percentage values in the closed interval [0.0, 1.0].

        If a `CustomColor` object with the given color is already
        present, it will be returned.  Otherwise, `addColor` will be
        called, and the new object is returned.

        If the optional parameter `similarity` is > 0.0, getColor()
        will return the first color found whose RGB difference's
        magnitude is < `similarity`, if any (otherwise, it will call
        `addColor()`, exactly as if similarity was not used).  This is
        useful if you expect many thousands of slightly different
        colors, which are not supported by XFig (the current format
        supports 512 custom colors).

        If `similarity` is given, but not > 0.0, `addColor()` will
        *not* be called, but a `KeyError` will be raised, if the exact
        color cannot be returned."""

        inputGiven = color

        # convert grayvalues to RGB triples:
        if isinstance(color, (float, int)):
            color = (color, color, color)

        # accept colors as 3-tuples of (0..255)
        if isinstance(color, tuple):
            # convert 0..1 floats to 0..255 integers:
            if isinstance(color[0], float):
                color = (int(round((color[0] * 255))),
                         int(round((color[1] * 255))),
                         int(round((color[2] * 255))))
            color = "#%02x%02x%02x" % color

        # accept any iterable RGB color objects, too:
        if not isinstance(color, str):
            color = "#%02x%02x%02x" % tuple(color)

        assert len(color) == 7, \
            "too large values given for red, green, or blue: %s" % (inputGiven,)

        result = self._colorhash.get(color, None)
        if result != None:
            return result

        if similarity == None:
            return self.addColor(color)

        if not similarity > 0.0:
            raise KeyError("getColor(%s): no similar color found" % color)

        if self.colors:  # don't choke when there are no colors yet
            def rgbDiffSortTuple(otherRGB,
                                 searchRGB=CustomColor(None, color)):
                return sum(map(lambda x: x * x, searchRGB - otherRGB)), otherRGB

            matches = map(rgbDiffSortTuple, self.colors)
            matches.sort()
            bestSqDiff, bestColor = matches[0]
            if bestSqDiff < similarity * similarity:
                return bestColor

        return self.addColor(color)

    def colorRGB(self, colorIndex):
        """Return a the R,G,B tuple for the given color index.
        (With values from the range 0..255.)"""

        assert colorIndex >= 0 and colorIndex < Color.Custom0 + len(self.colors), \
            "invalid color index %d" % colorIndex
        if colorIndex < Color.Custom0:
            return standardColors[colorIndex]
        else:
            return self.colors[colorIndex - Color.Custom0].rgb()

    def gray(self, grayLevel):
        """Return a color representing the given graylevel (see
        getColor).  grayLevel can be a float in the range 0.0 - 1.0 or
        a 0 - 255 integer."""

        return self.getColor((grayLevel, grayLevel, grayLevel))

    def headerStr(self):
        """Return the first lines of the XFig file output, which contain
        global document information like orientation / units / ..."""

        result = "#FIG 3.2\n"
        if self.landscape:
            result += "Landscape\n"
        else:
            result += "Portrait\n"
        if self.centered:
            result += "Center\n"
        else:
            result += "Flush Left\n"
        if self.metric:
            result += "Metric\n"
        else:
            result += "Inches\n"
        result += self.paperSize + "\n"
        result += str(self.magnification) + "\n"
        if self.singlePage:
            result += "Single\n"
        else:
            result += "Multiple\n"
        result += str(self.transparentColor) + "\n"
        result += _formatComment(self.comment)
        result += str(self.ppi) + " 2\n"  # (2: only used coordinate system)
        return result

    def objectsStr(self):
        """figfile.objectsStr()

        Returns the part of the XFig file containing all objects
        (but not the custom colors).  This is the same as str(object)
        concatenated for each object in `figfile`."""

        return "".join(map(str, self))

    def __str__(self):
        """Return the contents of this file as string in the XFig file format.
        See save()."""

        assert len(self.colors) < 512, \
            ".fig file format does not allow more than 512 custom colors!"
        result = self.headerStr() + \
                 "".join(map(repr, self.colors)) + \
                 self.objectsStr()
        return result

    def save(self, filename=None, fig2dev=None):
        """figfile.save(filename = None)

        Saves the contents of this file in the XFig file format to
        the file 'filename'.  Equivalent to::

          file(filename, "w").write(str(figfile))

        If filename is not given, and figfile was constructed from an
        existing file, that one is overwritten (-> figfile.filename).
        If the filename does not end in '.fig', the extension is
        appended.

        After saving, the filename becomes the new figfile.filename
        and would be used for the next save() without filename.

        The return value is the output file written last, i.e. it
        depends on whether fig2dev was given:

        - if fig2dev == None (default), figfile.filename is returned
        - otherwise, the exported filename is returned (e.g. basename.eps)"""

        if filename != None:
            if not filename.endswith(".fig"):
                filename += ".fig"
            self.filename = filename
        assert self.filename, "figfile.save() needs a filename!"

        # construct whole string in memory for exception safety:
        output = str(self)
        # everything's fine, *now* write to file:
        file(self.filename, "w").write(output)

        if fig2dev:
            return self.fig2dev(lang=fig2dev)

        return self.filename

    def fig2dev(self, input=None, output=None, lang="eps"):
        """figfile.fig2dev(input = None, output = None, lang = "eps")

        Calls fig2dev on the file `input` to produce the file `output`.
        (Both default to the current figfile's filename and the same
        filename with the extension changed to `lang`.)
        Note that `output` must be a path *relative to the `input` path*!
        Returns the filename of the resulting file.

        Usually, you just call sth. like ::

           figfile = fig.File("myfigfile.fig")
           ...
           figfile.save()
           figfile.fig2dev(lang = "pdf")

        to produce myfigfile.pdf.  It is now even easier to use the
        following convenience shortcut::

           figfile.save(fig2dev = "pdf")
        """

        if input == None:
            input = self.filename

        path, basename = os.path.split(input)

        if not output:
            output = basename
            if output.endswith(".fig"):
                output = output[:-4]
            output += "." + lang

        oldcwd = None
        if path:
            oldcwd = os.path.abspath(".")
            os.chdir(path)

        try:
            outFile = file(output, "w")
            try:
                import subprocess
            except ImportError:
                cin, cout = os.popen4("fig2dev -L %s '%s'" % (lang, basename))
                cin.close()
                outFile.write(cout.read())
                cout.close()
            else:
                subprocess.call(["fig2dev", "-L", lang, basename],
                                stdout=outFile)
            outFile.close()
        finally:
            if oldcwd:
                os.chdir(oldcwd)

        return os.path.normpath(os.path.join(path, output))


# --------------------------------------------------------------------

def copyObjects(fileA, fileB):
    colorMap = {}
    for color in fileA.colors:
        colorMap[int(color)] = fileB.getColor(color.hexCode)

    for o in fileA.allObjects():
        o = copy.deepcopy(o)
        if o.penColor >= Color.Custom0:
            o.penColor = colorMap[int(o.penColor)]
        if o.fillColor >= Color.Custom0:
            o.fillColor = colorMap[int(o.fillColor)]
        fileB.append(o)


# --------------------------------------------------------------------
#                              TESTING:
# --------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        def normalize(text):
            result = []
            for line in text.split("\n"):
                # canonical float representation:
                result.append(re.sub(r"(\.[0-9]+?)0*\b", r"\1", line.strip()))
            return result


        import difflib, re

        for fn in sys.argv[1:]:
            input = normalize(file(fn).read())
            output = normalize(str(File(fn)))
            #           for line in difflib.unified_diff(input, output):
            #               print line
            sm = difflib.SequenceMatcher(None, input, output)
            for code, b1, e1, b2, e2 in sm.get_opcodes():
                if code == 'equal':
                    continue
                for li in range(b1, e1):
                    print("-", input[li])
                for li in range(b2, e2):
                    print("+", output[li])


    else:
        import doctest

        doctest.testfile('index.rst')