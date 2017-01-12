/***************************************************************************
  qgspallabeling.h
  Smart labeling for vector layers
  -------------------
   begin                : June 2009
   copyright            : (C) Martin Dobias
   email                : wonder dot sk at gmail dot com

 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

//Note: although this file is in the core library, it is not part of the stable API
//and might change at any time!

#ifndef QGSPALLABELING_H
#define QGSPALLABELING_H

#include "qgis_core.h"
#include <QString>
#include <QFont>
#include <QFontDatabase>
#include <QColor>
#include <QHash>
#include <QList>
#include <QPainter>
#include <QRectF>
#include "qgsfeature.h"
#include "qgsgeometry.h"
#include "qgsfields.h"
#include "qgspoint.h"
#include "qgsmapunitscale.h"
#include "qgsstringutils.h"
#include "qgstextrenderer.h"

namespace pal
{
  class Pal;
  class Layer;
  class LabelPosition;
}

class QgsDiagramLayerSettings;
class QgsRectangle;
class QgsMapToPixel;
class QgsFeature;
class QgsTextLabelFeature;
class QgsVectorLayer;
class QgsDataDefined;
class QgsExpression;
class QFontMetricsF;
class QPainter;
class QPicture;
class QgsGeometry;
class QgsCoordinateTransform;
class QgsLabelSearchTree;
class QgsMapSettings;
class QgsLabelFeature;
class QgsLabelingEngine;
class QgsPalLayerSettings;
class QgsVectorLayerLabelProvider;
class QgsDxfExport;
class QgsVectorLayerDiagramProvider;



/** \ingroup core
 * \class QgsLabelPosition
 */
class CORE_EXPORT QgsLabelPosition
{
  public:
    QgsLabelPosition( int id, double r, const QVector< QgsPoint >& corners, const QgsRectangle& rect, double w, double h, const QString& layer, const QString& labeltext, const QFont& labelfont, bool upside_down, bool diagram = false, bool pinned = false, const QString& providerId = QString() )
        : featureId( id )
        , rotation( r )
        , cornerPoints( corners )
        , labelRect( rect )
        , width( w )
        , height( h )
        , layerID( layer )
        , labelText( labeltext )
        , labelFont( labelfont )
        , upsideDown( upside_down )
        , isDiagram( diagram )
        , isPinned( pinned )
        , providerID( providerId )
    {}
    QgsLabelPosition()
        : featureId( -1 )
        , rotation( 0 )
        , labelRect( QgsRectangle() )
        , width( 0 )
        , height( 0 )
        , layerID( QLatin1String( "" ) )
        , labelText( QLatin1String( "" ) )
        , labelFont( QFont() )
        , upsideDown( false )
        , isDiagram( false )
        , isPinned( false )
    {}
    int featureId;
    double rotation;
    QVector< QgsPoint > cornerPoints;
    QgsRectangle labelRect;
    double width;
    double height;
    QString layerID;
    QString labelText;
    QFont labelFont;
    bool upsideDown;
    bool isDiagram;
    bool isPinned;
    //! @note added in 2.14
    QString providerID;
};


/** \ingroup core
 * \class QgsPalLayerSettings
 */
class CORE_EXPORT QgsPalLayerSettings
{
  public:
    QgsPalLayerSettings();
    QgsPalLayerSettings( const QgsPalLayerSettings& s );
    ~QgsPalLayerSettings();

    //! copy operator - only copies the permanent members
    QgsPalLayerSettings &operator=( const QgsPalLayerSettings & s );

    //! @note added in 2.4
    static QgsPalLayerSettings fromLayer( QgsVectorLayer* layer );

    /** Placement modes which determine how label candidates are generated for a feature.
     */
    //TODO QGIS 3.0 - move to QgsLabelingEngine
    enum Placement
    {
      AroundPoint, //!< Arranges candidates in a circle around a point (or centroid of a polygon). Applies to point or polygon layers only.
      OverPoint, //! Arranges candidates over a point (or centroid of a polygon), or at a preset offset from the point. Applies to point or polygon layers only.
      Line, //!< Arranges candidates parallel to a generalised line representing the feature or parallel to a polygon's perimeter. Applies to line or polygon layers only.
      Curved, //! Arranges candidates following the curvature of a line feature. Applies to line layers only.
      Horizontal, //!< Arranges horizontal candidates scattered throughout a polygon feature. Applies to polygon layers only.
      Free, //!< Arranges candidates scattered throughout a polygon feature. Candidates are rotated to respect the polygon's orientation. Applies to polygon layers only.
      OrderedPositionsAroundPoint, //!< Candidates are placed in predefined positions around a point. Preference is given to positions with greatest cartographic appeal, e.g., top right, bottom right, etc. Applies to point layers only.
      PerimeterCurved, //! Arranges candidates following the curvature of a polygon's boundary. Applies to polygon layers only.
    };

    //! Positions for labels when using the QgsPalLabeling::OrderedPositionsAroundPoint placement mode
    //TODO QGIS 3.0 - move to QgsLabelingEngine
    enum PredefinedPointPosition
    {
      TopLeft, //!< Label on top-left of point
      TopSlightlyLeft, //! Label on top of point, slightly left of center
      TopMiddle, //!< Label directly above point
      TopSlightlyRight, //! Label on top of point, slightly right of center
      TopRight, //!< Label on top-right of point
      MiddleLeft, //!< Label on left of point
      MiddleRight, //!< Label on right of point
      BottomLeft, //!< Label on bottom-left of point
      BottomSlightlyLeft, //! Label below point, slightly left of center
      BottomMiddle, //!< Label directly below point
      BottomSlightlyRight, //! Label below point, slightly right of center
      BottomRight, //!< Label on bottom right of point
    };

    //! Behavior modifier for label offset and distance, only applies in some
    //! label placement modes.
    //TODO QGIS 3.0 - move to QgsLabelingEngine
    enum OffsetType
    {
      FromPoint, //!< Offset distance applies from point geometry
      FromSymbolBounds, //!< Offset distance applies from rendered symbol bounds
    };

    /** Line placement flags, which control how candidates are generated for a linear feature.
     */
    //TODO QGIS 3.0 - move to QgsLabelingEngine, rename to LinePlacementFlag, use Q_DECLARE_FLAGS to make
    //LinePlacementFlags type, and replace use of pal::LineArrangementFlag
    enum LinePlacementFlags
    {
      OnLine    = 1,      //!< Labels can be placed directly over a line feature.
      AboveLine = 2,      /**< Labels can be placed above a line feature. Unless MapOrientation is also specified this mode
                               respects the direction of the line feature, so a line from right to left labels will have labels
                               placed placed below the line feature. */
      BelowLine = 4,      /**< Labels can be placed below a line feature. Unless MapOrientation is also specified this mode
                               respects the direction of the line feature, so a line from right to left labels will have labels
                               placed placed above the line feature. */
      MapOrientation = 8, /**< Signifies that the AboveLine and BelowLine flags should respect the map's orientation rather
                               than the feature's orientation. For example, AboveLine will always result in label's being placed
                               above a line, regardless of the line's direction. */
    };

    enum QuadrantPosition
    {
      QuadrantAboveLeft,
      QuadrantAbove,
      QuadrantAboveRight,
      QuadrantLeft,
      QuadrantOver,
      QuadrantRight,
      QuadrantBelowLeft,
      QuadrantBelow,
      QuadrantBelowRight
    };

    enum UpsideDownLabels
    {
      Upright, //!< Upside-down labels (90 <= angle < 270) are shown upright
      ShowDefined, //!< Show upside down when rotation is layer- or data-defined
      ShowAll //!< Show upside down for all labels, including dynamic ones
    };

    enum DirectionSymbols
    {
      SymbolLeftRight, //!< Place direction symbols on left/right of label
      SymbolAbove, //!< Place direction symbols on above label
      SymbolBelow //!< Place direction symbols on below label
    };

    enum MultiLineAlign
    {
      MultiLeft = 0,
      MultiCenter,
      MultiRight,
      MultiFollowPlacement /*!< Alignment follows placement of label, e.g., labels to the left of a feature
                               will be drawn with right alignment*/
    };

    /** Valid obstacle types, which affect how features within the layer will act as obstacles
     * for labels.
     */
    //TODO QGIS 3.0 - Move to QgsLabelingEngine
    enum ObstacleType
    {
      PolygonInterior, /*!< avoid placing labels over interior of polygon (prefer placing labels totally
       outside or just slightly inside polygon) */
      PolygonBoundary, /*!< avoid placing labels over boundary of polygon (prefer placing outside or
       completely inside polygon) */
      PolygonWhole /*!< avoid placing labels over ANY part of polygon. Where PolygonInterior will prefer
       to place labels with the smallest area of intersection between the label and the polygon,
       PolygonWhole will penalise any label which intersects with the polygon by an equal amount, so that
       placing labels over any part of the polygon is avoided.*/
    };


    //! Units used for option sizes, before being converted to rendered sizes
    enum SizeUnit
    {
      Points = 0,
      MM,
      MapUnits,
      Percent
    };

    // update mDataDefinedNames QMap in constructor when adding/deleting enum value
    enum DataDefinedProperties
    {
      // text style
      Size = 0,
      Bold = 1,
      Italic = 2,
      Underline = 3,
      Color = 4,
      Strikeout = 5,
      Family = 6,
      FontStyle = 21,
      FontSizeUnit = 22,
      FontTransp = 18,
      FontCase = 27,
      FontLetterSpacing = 28,
      FontWordSpacing = 29,
      FontBlendMode = 30,

      // text formatting
      MultiLineWrapChar = 31,
      MultiLineHeight = 32,
      MultiLineAlignment = 33,
      DirSymbDraw = 34,
      DirSymbLeft = 35,
      DirSymbRight = 36,
      DirSymbPlacement = 37,
      DirSymbReverse = 38,
      NumFormat = 39,
      NumDecimals = 40,
      NumPlusSign = 41,

      // text buffer
      BufferDraw = 42,
      BufferSize = 7,
      BufferUnit = 43,
      BufferColor = 8,
      BufferTransp = 19,
      BufferJoinStyle = 44,
      BufferBlendMode = 45,

      // background
      ShapeDraw = 46,
      ShapeKind = 47,
      ShapeSVGFile = 48,
      ShapeSizeType = 49,
      ShapeSizeX = 50,
      ShapeSizeY = 85,
      ShapeSizeUnits = 51,
      ShapeRotationType = 52,
      ShapeRotation = 53,
      ShapeOffset = 54,
      ShapeOffsetUnits = 55,
      ShapeRadii = 56,
      ShapeRadiiUnits = 57,
      ShapeTransparency = 63,
      ShapeBlendMode = 64,
      ShapeFillColor = 58,
      ShapeBorderColor = 59,
      ShapeBorderWidth = 60,
      ShapeBorderWidthUnits = 61,
      ShapeJoinStyle = 62,

      // drop shadow
      ShadowDraw = 65,
      ShadowUnder = 66,
      ShadowOffsetAngle = 67,
      ShadowOffsetDist = 68,
      ShadowOffsetUnits = 69,
      ShadowRadius = 70,
      ShadowRadiusUnits = 71,
      ShadowTransparency = 72,
      ShadowScale = 73,
      ShadowColor = 74,
      ShadowBlendMode = 75,

      // placement
      CentroidWhole = 76,
      OffsetQuad = 77,
      OffsetXY = 78,
      OffsetUnits = 80,
      LabelDistance = 13,
      DistanceUnits = 81,
      OffsetRotation = 82,
      CurvedCharAngleInOut = 83,
      // (data defined only)
      PositionX = 9, //x-coordinate data defined label position
      PositionY = 10, //y-coordinate data defined label position
      Hali = 11, //horizontal alignment for data defined label position (Left, Center, Right)
      Vali = 12, //vertical alignment for data defined label position (Bottom, Base, Half, Cap, Top)
      Rotation = 14, //data defined rotation
      RepeatDistance = 84,
      RepeatDistanceUnit = 86,
      Priority = 87,
      PredefinedPositionOrder = 91,

      // rendering
      ScaleVisibility = 23,
      MinScale = 16,
      MaxScale = 17,
      FontLimitPixel = 24,
      FontMinPixel = 25,
      FontMaxPixel = 26,
      IsObstacle = 88,
      ObstacleFactor = 89,
      ZIndex = 90,

      // (data defined only)
      Show = 15,
      AlwaysShow = 20
    };

    // whether to label this layer
    bool enabled;

    /** Whether to draw labels for this layer. For some layers it may be desirable
     * to register their features as obstacles for other labels without requiring
     * labels to be drawn for the layer itself. In this case drawLabels can be set
     * to false and obstacle set to true, which will result in the layer acting
     * as an obstacle but having no labels of its own.
     * @note added in QGIS 2.12
     */
    bool drawLabels;

    //-- text style

    QString fieldName;

    /** Is this label made from a expression string, e.g., FieldName || 'mm'
      */
    bool isExpression;

    /** Returns the QgsExpression for this label settings.
      */
    QgsExpression* getLabelExpression();

    QColor previewBkgrdColor;

    //! Substitution collection for automatic text substitution with labels
    QgsStringReplacementCollection substitutions;
    //! True if substitutions should be applied
    bool useSubstitutions;

    //-- text formatting

    QString wrapChar;
    MultiLineAlign multilineAlign; // horizontal alignment of multi-line labels

    // Adds '<' or '>', or user-defined symbol to the label string pointing to the
    // direction of the line / polygon ring
    // Works only if Placement == Line
    bool addDirectionSymbol;
    QString leftDirectionSymbol;
    QString rightDirectionSymbol;
    DirectionSymbols placeDirectionSymbol; // whether to place left/right, above or below label
    bool reverseDirectionSymbol;

    bool formatNumbers;
    int decimals;
    bool plusSign;

    //-- placement

    Placement placement;
    unsigned int placementFlags;

    bool centroidWhole; // whether centroid calculated from whole or visible polygon
    bool centroidInside; // whether centroid-point calculated must be inside polygon

    /** Ordered list of predefined label positions for points. Positions earlier
     * in the list will be prioritized over later positions. Only used when the placement
     * is set to QgsPalLayerSettings::OrderedPositionsAroundPoint.
     * @note not available in Python bindings
     */
    QVector< PredefinedPointPosition > predefinedPositionOrder;

    /** True if only labels which completely fit within a polygon are allowed.
     */
    bool fitInPolygonOnly;
    double dist; // distance from the feature (in mm)
    bool distInMapUnits; //true if distance is in map units (otherwise in mm)
    QgsMapUnitScale distMapUnitScale;
    //! Offset type for layer (only applies in certain placement modes)
    OffsetType offsetType;

    double repeatDistance;
    SizeUnit repeatDistanceUnit;
    QgsMapUnitScale repeatDistanceMapUnitScale;

    // offset labels of point/centroid features default to center
    // move label to quadrant: left/down, don't move, right/up (-1, 0, 1)
    QuadrantPosition quadOffset;

    double xOffset; // offset from point in mm or map units
    double yOffset; // offset from point in mm or map units
    bool labelOffsetInMapUnits; //true if label offset is in map units (otherwise in mm)
    QgsMapUnitScale labelOffsetMapUnitScale;
    double angleOffset; // rotation applied to offset labels
    bool preserveRotation; // preserve predefined rotation data during label pin/unpin operations

    double maxCurvedCharAngleIn; // maximum angle between inside curved label characters (defaults to 20.0, range 20.0 to 60.0)
    double maxCurvedCharAngleOut; // maximum angle between outside curved label characters (defaults to -20.0, range -20.0 to -95.0)

    int priority; // 0 = low, 10 = high

    //-- rendering

    bool scaleVisibility;
    int scaleMin;
    int scaleMax;

    bool fontLimitPixelSize; // true is label should be limited by fontMinPixelSize/fontMaxPixelSize
    int fontMinPixelSize; // minimum pixel size for showing rendered map unit labels (1 - 1000)
    int fontMaxPixelSize; // maximum pixel size for showing rendered map unit labels (1 - 10000)

    bool displayAll;  // if true, all features will be labelled even though overlaps occur
    UpsideDownLabels upsidedownLabels; // whether, or how, to show upsidedown labels

    bool labelPerPart; // whether to label every feature's part or only the biggest one
    bool mergeLines;

    bool limitNumLabels; // whether to limit the number of labels to be drawn
    int maxNumLabels; // maximum number of labels to be drawn

    double minFeatureSize; // minimum feature size to be labelled (in mm)
    bool obstacle; // whether features for layer are obstacles to labels of other layers

    /** Obstacle factor, where 1.0 = default, < 1.0 more likely to be covered by labels,
     * > 1.0 less likely to be covered
     */
    double obstacleFactor;

    /** Controls how features act as obstacles for labels
     */
    ObstacleType obstacleType;

    //! Z-Index of label, where labels with a higher z-index are rendered on top of labels with a lower z-index
    double zIndex;

    // called from register feature hook
    void calculateLabelSize( const QFontMetricsF* fm, QString text, double& labelX, double& labelY, QgsFeature* f = nullptr, QgsRenderContext* context = nullptr );

    /** Register a feature for labeling.
     * @param f feature to label
     * @param context render context. The QgsExpressionContext contained within the render context
     * must have already had the feature and fields sets prior to calling this method.
     * @param labelFeature if using QgsLabelingEngine, this will receive the label feature. Not available
     * in Python bindings.
     * @param obstacleGeometry optional obstacle geometry, if a different geometry to the feature's geometry
     * should be used as an obstacle for labels (e.g., if the feature has been rendered with an offset point
     * symbol, the obstacle geometry should represent the bounds of the offset symbol). If not set,
     * the feature's original geometry will be used as an obstacle for labels. Not available
     * in Python bindings.
     */
    void registerFeature( QgsFeature& f, QgsRenderContext& context, QgsLabelFeature** labelFeature = nullptr, QgsGeometry* obstacleGeometry = nullptr );

    void readFromLayer( QgsVectorLayer* layer );
    void writeToLayer( QgsVectorLayer* layer );

    /** Read settings from a DOM element
     * @note added in 2.12
     */
    void readXml( QDomElement& elem );

    /** Write settings into a DOM element
     * @note added in 2.12
     */
    QDomElement writeXml( QDomDocument& doc );

    /** Get a data defined property pointer
     * @note helpful for Python access
     */
    QgsDataDefined* dataDefinedProperty( QgsPalLayerSettings::DataDefinedProperties p );

    /** Set a property as data defined
     * @note helpful for Python access
     */
    void setDataDefinedProperty( QgsPalLayerSettings::DataDefinedProperties p,
                                 bool active, bool useExpr, const QString& expr, const QString& field );

    //! Set a property to static instead data defined
    void removeDataDefinedProperty( QgsPalLayerSettings::DataDefinedProperties p );

    /** Clear all data-defined properties
     * @note added in QGIS 2.12
     */
    void removeAllDataDefinedProperties();

    /** Convert old property value to new one as delimited values
     * @note not available in python bindings; as temporary solution until refactoring of project settings
     */
    QString updateDataDefinedString( const QString& value );

    /** Get property value as separate values split into Qmap
     * @note not available in python bindings
     */
    QMap<QString, QString> dataDefinedMap( QgsPalLayerSettings::DataDefinedProperties p ) const;

    /** Get data defined property value from expression string or attribute field name
     * @returns value inside QVariant
     * @note not available in python bindings
     */
    QVariant dataDefinedValue( QgsPalLayerSettings::DataDefinedProperties p, QgsFeature& f, const QgsFields& fields,
                               const QgsExpressionContext* context = nullptr ) const;

    /** Get data defined property value from expression string or attribute field name
     * @returns true/false whether result is null or invalid
     * @note not available in python bindings
     */
    bool dataDefinedEvaluate( QgsPalLayerSettings::DataDefinedProperties p, QVariant& exprVal, QgsExpressionContext* context = nullptr, const QVariant& originalValue = QVariant() ) const;

    /** Whether data definition is active
     */
    bool dataDefinedIsActive( QgsPalLayerSettings::DataDefinedProperties p ) const;

    /** Whether data definition is set to use an expression
     */
    bool dataDefinedUseExpression( QgsPalLayerSettings::DataDefinedProperties p ) const;

    /** Map of current data defined properties
     *
     * Pointers to QgsDataDefined should never be null, the pointers are owned by this class
     */
    QMap< QgsPalLayerSettings::DataDefinedProperties, QgsDataDefined* > dataDefinedProperties;

    /** Map of data defined enum to names and old-style indecies
     * The QPair contains a new string for layer property key, and a reference to old-style numeric key (< QGIS 2.0)
     * @note not available in python bindings;
     */
    QMap<QgsPalLayerSettings::DataDefinedProperties, QPair<QString, int> > dataDefinedNames() const { return mDataDefinedNames; }

    /** Returns the label text formatting settings, e.g., font settings, buffer settings, etc.
     * @see setFormat()
     * @note added in QGIS 3.0
     */
    const QgsTextFormat& format() const { return mFormat; }

    /** Sets the label text formatting settings, e.g., font settings, buffer settings, etc.
     * @param format label text format
     * @see format()
     * @note added in QGIS 3.0
     */
    void setFormat( const QgsTextFormat& format ) { mFormat = format; }

    // temporary stuff: set when layer gets prepared or labeled
    QgsFeature* mCurFeat;
    QgsFields mCurFields;
    int fieldIndex;
    const QgsMapToPixel* xform;
    QgsCoordinateTransform ct;

    QgsPoint ptZero;
    QgsPoint ptOne;
    QgsGeometry extentGeom;
    int mFeaturesToLabel; // total features that will probably be labeled, may be less (figured before PAL)
    int mFeatsSendingToPal; // total features tested for sending into PAL (relative to maxNumLabels)
    int mFeatsRegPal; // number of features registered in PAL, when using limitNumLabels

  private:

    void readDataDefinedPropertyMap( QgsVectorLayer* layer, QDomElement* parentElem,
                                     QMap < QgsPalLayerSettings::DataDefinedProperties,
                                     QgsDataDefined* > & propertyMap );
    void writeDataDefinedPropertyMap( QgsVectorLayer* layer, QDomElement* parentElem,
                                      const QMap < QgsPalLayerSettings::DataDefinedProperties,
                                      QgsDataDefined* > & propertyMap );
    void readDataDefinedProperty( QgsVectorLayer* layer,
                                  QgsPalLayerSettings::DataDefinedProperties p,
                                  QMap < QgsPalLayerSettings::DataDefinedProperties,
                                  QgsDataDefined* > & propertyMap );

    enum DataDefinedValueType
    {
      DDBool,
      DDInt,
      DDIntPos,
      DDDouble,
      DDDoublePos,
      DDRotation180,
      DDTransparency,
      DDString,
      DDUnits,
      DDColor,
      DDJoinStyle,
      DDBlendMode,
      DDPointF
    };

    // convenience data defined evaluation function
    bool dataDefinedValEval( DataDefinedValueType valType,
                             QgsPalLayerSettings::DataDefinedProperties p,
                             QVariant& exprVal, QgsExpressionContext &context, const QVariant& originalValue = QVariant() );

    void parseTextStyle( QFont& labelFont,
                         QgsUnitTypes::RenderUnit fontunits,
                         QgsRenderContext& context );

    void parseTextBuffer( QgsRenderContext& context );

    void parseTextFormatting( QgsRenderContext& context );

    void parseShapeBackground( QgsRenderContext& context );

    void parseDropShadow( QgsRenderContext& context );

    /** Checks if a feature is larger than a minimum size (in mm)
    @return true if above size, false if below*/
    bool checkMinimumSizeMM( const QgsRenderContext& ct, const QgsGeometry& geom, double minSize ) const;

    /** Registers a feature as an obstacle only (no label rendered)
     */
    void registerObstacleFeature( QgsFeature &f, QgsRenderContext &context, QgsLabelFeature** obstacleFeature, QgsGeometry* obstacleGeometry = nullptr );

    QMap<DataDefinedProperties, QVariant> dataDefinedValues;
    QgsExpression* expression;
    QMap<QgsPalLayerSettings::DataDefinedProperties, QPair<QString, int> > mDataDefinedNames;

    QFontDatabase mFontDB;

    QgsTextFormat mFormat;

    static QVector< PredefinedPointPosition > DEFAULT_PLACEMENT_ORDER;
};

/** \ingroup core
 */
class CORE_EXPORT QgsLabelCandidate
{
  public:
    QgsLabelCandidate( const QRectF& r, double c ): rect( r ), cost( c ) {}

    QRectF rect;
    double cost;
};




/** \ingroup core
 * Class that stores computed placement from labeling engine.
 * @note added in 2.4
 */
class CORE_EXPORT QgsLabelingResults
{
  public:
    QgsLabelingResults();
    ~QgsLabelingResults();

    //! QgsLabelingResults cannot be copied.
    QgsLabelingResults( const QgsLabelingResults& ) = delete;
    //! QgsLabelingResults cannot be copied.
    QgsLabelingResults& operator=( const QgsLabelingResults& rh ) = delete;

    //! return infos about labels at a given (map) position
    QList<QgsLabelPosition> labelsAtPosition( const QgsPoint& p ) const;
    //! return infos about labels within a given (map) rectangle
    QList<QgsLabelPosition> labelsWithinRect( const QgsRectangle& r ) const;

  private:

    QgsLabelSearchTree* mLabelSearchTree;

    friend class QgsPalLabeling;
    friend class QgsVectorLayerLabelProvider;
    friend class QgsVectorLayerDiagramProvider;
};

/** \ingroup core
 * \class QgsPalLabeling
 */
class CORE_EXPORT QgsPalLabeling
{
  public:

    QgsPalLabeling();
    ~QgsPalLabeling();

    void numCandidatePositions( int& candPoint, int& candLine, int& candPolygon );
    void setNumCandidatePositions( int candPoint, int candLine, int candPolygon );

    enum Search { Chain, Popmusic_Tabu, Popmusic_Chain, Popmusic_Tabu_Chain, Falp };

    void setSearchMethod( Search s );
    Search searchMethod() const;

    bool isShowingCandidates() const;
    void setShowingCandidates( bool showing );

    bool isShowingAllLabels() const;
    void setShowingAllLabels( bool showing );

    bool isShowingPartialsLabels() const;
    void setShowingPartialsLabels( bool showing );

    //! @note added in 2.4
    bool isDrawingOutlineLabels() const;
    void setDrawingOutlineLabels( bool outline );

    /** Returns whether the engine will only draw the outline rectangles of labels,
     * not the label contents themselves. Used for debugging and testing purposes.
     * @see setDrawLabelRectOnly
     * @note added in QGIS 2.12
     */
    bool drawLabelRectOnly() const;

    /** Sets whether the engine should only draw the outline rectangles of labels,
     * not the label contents themselves. Used for debugging and testing purposes.
     * @param drawRect set to true to enable rect drawing only
     * @see drawLabelRectOnly
     * @note added in QGIS 2.12
     */
    void setDrawLabelRectOnly( bool drawRect );

    //! called to find out whether the layer is used for labeling
    //! @note added in 2.4
    static bool staticWillUseLayer( QgsVectorLayer* layer );
    static bool staticWillUseLayer( const QString& layerID );

    //! @note not available in python bindings
    static void drawLabelCandidateRect( pal::LabelPosition* lp, QPainter* painter, const QgsMapToPixel* xform, QList<QgsLabelCandidate>* candidates = nullptr );

    //! load/save engine settings to project file
    void loadEngineSettings();
    void saveEngineSettings();
    void clearEngineSettings();

    /** Prepares a geometry for registration with PAL. Handles reprojection, rotation, clipping, etc.
     * @param geometry geometry to prepare
     * @param context render context
     * @param ct coordinate transform, or invalid transform if no transformation required
     * @param clipGeometry geometry to clip features to, if applicable
     * @returns prepared geometry
     * @note added in QGIS 2.9
     */
    static QgsGeometry prepareGeometry( const QgsGeometry& geometry, QgsRenderContext &context, const QgsCoordinateTransform& ct, QgsGeometry *clipGeometry = nullptr );

    /** Checks whether a geometry requires preparation before registration with PAL
     * @param geometry geometry to prepare
     * @param context render context
     * @param ct coordinate transform, or invalid transform if no transformation required
     * @param clipGeometry geometry to clip features to, if applicable
     * @returns true if geometry requires preparation
     * @note added in QGIS 2.9
     */
    static bool geometryRequiresPreparation( const QgsGeometry& geometry, QgsRenderContext &context, const QgsCoordinateTransform& ct, QgsGeometry *clipGeometry = nullptr );

    /** Splits a text string to a list of separate lines, using a specified wrap character.
     * The text string will be split on either newline characters or the wrap character.
     * @param text text string to split
     * @param wrapCharacter additional character to wrap on
     * @returns list of text split to lines
     * @note added in QGIS 2.9
     */
    static QStringList splitToLines( const QString& text, const QString& wrapCharacter );

    /** Splits a text string to a list of graphemes, which are the smallest allowable character
     * divisions in the string. This accounts for scripts were individual characters are not
     * allowed to be split apart (e.g., Arabic and Indic based scripts)
     * @param text string to split
     * @returns list of graphemes
     * @note added in QGIS 2.10
     */
    static QStringList splitToGraphemes( const QString& text );

  protected:
    // update temporary QgsPalLayerSettings with any data defined text style values
    static void dataDefinedTextStyle( QgsPalLayerSettings& tmpLyr,
                                      const QMap< QgsPalLayerSettings::DataDefinedProperties, QVariant >& ddValues );

    // update temporary QgsPalLayerSettings with any data defined text formatting values
    static void dataDefinedTextFormatting( QgsPalLayerSettings& tmpLyr,
                                           const QMap< QgsPalLayerSettings::DataDefinedProperties, QVariant >& ddValues );

    // update temporary QgsPalLayerSettings with any data defined text buffer values
    static void dataDefinedTextBuffer( QgsPalLayerSettings& tmpLyr,
                                       const QMap< QgsPalLayerSettings::DataDefinedProperties, QVariant >& ddValues );

    // update temporary QgsPalLayerSettings with any data defined shape background values
    static void dataDefinedShapeBackground( QgsPalLayerSettings& tmpLyr,
                                            const QMap< QgsPalLayerSettings::DataDefinedProperties, QVariant >& ddValues );

    // update temporary QgsPalLayerSettings with any data defined drop shadow values
    static void dataDefinedDropShadow( QgsPalLayerSettings& tmpLyr,
                                       const QMap< QgsPalLayerSettings::DataDefinedProperties, QVariant >& ddValues );

    friend class QgsVectorLayerLabelProvider; // to allow calling the static methods above
    friend class QgsDxfExport;                // to allow calling the static methods above

    void deleteTemporaryData();

    /** Checks whether a geometry exceeds the minimum required size for a geometry to be labeled.
     * @param context render context
     * @param geom geometry
     * @param minSize minimum size for geometry
     * @returns true if geometry exceeds minimum size
     * @note added in QGIS 2.9
     */
    static bool checkMinimumSizeMM( const QgsRenderContext &context, const QgsGeometry *geom, double minSize );

    //! hashtable of label providers, being filled during labeling (key = layer ID)
    QHash<QString, QgsVectorLayerLabelProvider*> mLabelProviders;
    //! hashtable of diagram providers (key = layer ID)
    QHash<QString, QgsVectorLayerDiagramProvider*> mDiagramProviders;
    QgsPalLayerSettings mInvalidLayerSettings;

    //! New labeling engine to interface with PAL
    QgsLabelingEngine* mEngine;

    // list of candidates from last labeling
    QList<QgsLabelCandidate> mCandidates;

    friend class QgsPalLayerSettings;
};

#endif // QGSPALLABELING_H
