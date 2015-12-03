#include "qgsgeometrymodifiersymbollayerv2.h"
#include "qgsgeometry.h"

QgsSymbolLayerV2* QgsPolygonGeneratorSymbolLayer::create( const QgsStringMap& properties )
{
  return new QgsPolygonGeneratorSymbolLayer( QgsFillSymbolV2::createSimple( properties ), properties );
}

QgsPolygonGeneratorSymbolLayer::QgsPolygonGeneratorSymbolLayer( QgsFillSymbolV2* symbol, const QgsStringMap& properties )
    : QgsFillSymbolLayerV2( QgsSymbolV2::Fill )
    , mExpression( new QgsExpression( properties.value( "geometryModifier" ) ) )
    , mSymbol( symbol )
{
}

QString QgsPolygonGeneratorSymbolLayer::layerType() const
{
  return "PolygonGenerator";
}

void QgsPolygonGeneratorSymbolLayer::startRender( QgsSymbolV2RenderContext& context )
{
  mExpression->prepare( &context.expressionContext() );

  subSymbol()->startRender( context.renderContext() );
}

void QgsPolygonGeneratorSymbolLayer::stopRender( QgsSymbolV2RenderContext& context )
{
  if ( mSymbol )
    mSymbol->stopRender( context.renderContext() );
}

QgsSymbolLayerV2* QgsPolygonGeneratorSymbolLayer::clone() const
{
  QgsPolygonGeneratorSymbolLayer* clone = new QgsPolygonGeneratorSymbolLayer( mSymbol->clone() );
  clone->mExpression.reset( new QgsExpression( mExpression->expression() ) );

  return clone;
}

QgsStringMap QgsPolygonGeneratorSymbolLayer::properties() const
{
  QgsStringMap props;
  props.insert( "geometryModifier" , mExpression->expression() );
  return props;
}

void QgsPolygonGeneratorSymbolLayer::drawPreviewIcon( QgsSymbolV2RenderContext& context, QSize size )
{
  if ( mSymbol )
    mSymbol->drawPreviewIcon( context.renderContext().painter(), size );
}

void QgsPolygonGeneratorSymbolLayer::setGeometryModifier( const QString& exp )
{
  mExpression.reset( new QgsExpression( exp ) );
}

bool QgsPolygonGeneratorSymbolLayer::setSubSymbol( QgsSymbolV2* symbol )
{
  mSymbol = dynamic_cast<QgsFillSymbolV2*>( symbol );
  return true;
}

QSet<QString> QgsPolygonGeneratorSymbolLayer::usedAttributes() const
{
  return mSymbol->usedAttributes() + mExpression->referencedColumns().toSet();
}

bool QgsPolygonGeneratorSymbolLayer::isCompatibleWithSymbol( QgsSymbolV2* symbol )
{
  Q_UNUSED( symbol )
  return true;
}

void QgsPolygonGeneratorSymbolLayer::renderPolygon( const QPolygonF& points, QList<QPolygonF>* rings, QgsSymbolV2RenderContext& context )
{
  Q_UNUSED( points )
  Q_UNUSED( rings )

  QgsGeometry geom = mExpression->evaluate( &context.renderContext().expressionContext() ).value<QgsGeometry>();
  if ( context.feature() )
  {
    QgsFeature f = *context.feature();
    f.setGeometry( geom );

    mSymbol->renderFeature( f, context.renderContext() );
  }
}


