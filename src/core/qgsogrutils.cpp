/***************************************************************************
                             qgsogrutils.cpp
                             ---------------
    begin                : February 2016
    copyright            : (C) 2016 Nyall Dawson
    email                : nyall dot dawson at gmail dot com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include "qgsogrutils.h"
#include "qgsapplication.h"
#include "qgslogger.h"
#include "qgsgeometry.h"
#include "qgsfields.h"
#include <QTextCodec>
#include <QUuid>

QgsFeature QgsOgrUtils::readOgrFeature( OGRFeatureH ogrFet, const QgsFields& fields, QTextCodec* encoding )
{
  QgsFeature feature;
  if ( !ogrFet )
  {
    feature.setValid( false );
    return feature;
  }

  feature.setId( OGR_F_GetFID( ogrFet ) );
  feature.setValid( true );

  if ( !readOgrFeatureGeometry( ogrFet, feature ) )
  {
    feature.setValid( false );
  }

  if ( !readOgrFeatureAttributes( ogrFet, fields, feature, encoding ) )
  {
    feature.setValid( false );
  }

  return feature;
}

QgsFields QgsOgrUtils::readOgrFields( OGRFeatureH ogrFet, QTextCodec* encoding )
{
  QgsFields fields;

  if ( !ogrFet )
    return fields;

  int fieldCount = OGR_F_GetFieldCount( ogrFet );
  for ( int i = 0; i < fieldCount; ++i )
  {
    OGRFieldDefnH fldDef = OGR_F_GetFieldDefnRef( ogrFet, i );
    if ( !fldDef )
    {
      fields.append( QgsField() );
      continue;
    }

    QString name = encoding ? encoding->toUnicode( OGR_Fld_GetNameRef( fldDef ) ) : QString::fromUtf8( OGR_Fld_GetNameRef( fldDef ) );
    QVariant::Type varType;
    switch ( OGR_Fld_GetType( fldDef ) )
    {
      case OFTInteger:
        varType = QVariant::Int;
        break;
      case OFTInteger64:
        varType = QVariant::LongLong;
        break;
      case OFTReal:
        varType = QVariant::Double;
        break;
      case OFTDate:
        varType = QVariant::Date;
        break;
      case OFTTime:
        varType = QVariant::Time;
        break;
      case OFTDateTime:
        varType = QVariant::DateTime;
        break;
      case OFTString:
      default:
        varType = QVariant::String; // other unsupported, leave it as a string
    }
    fields.append( QgsField( name, varType ) );
  }
  return fields;
}

QVariant QgsOgrUtils::getOgrFeatureAttribute( OGRFeatureH ogrFet, const QgsFields& fields, int attIndex, QTextCodec* encoding , bool* ok )
{
  if ( !ogrFet || attIndex < 0 || attIndex >= fields.count() )
  {
    if ( ok )
      *ok = false;
    return QVariant();
  }

  OGRFieldDefnH fldDef = OGR_F_GetFieldDefnRef( ogrFet, attIndex );

  if ( ! fldDef )
  {
    if ( ok )
      *ok = false;

    QgsDebugMsg( "ogrFet->GetFieldDefnRef(attindex) returns NULL" );
    return QVariant();
  }

  QVariant value;

  if ( ok )
    *ok = true;

  if ( OGR_F_IsFieldSet( ogrFet, attIndex ) )
  {
    switch ( fields.at( attIndex ).type() )
    {
      case QVariant::String:
      {
        if ( encoding )
          value = QVariant( encoding->toUnicode( OGR_F_GetFieldAsString( ogrFet, attIndex ) ) );
        else
          value = QVariant( QString::fromUtf8( OGR_F_GetFieldAsString( ogrFet, attIndex ) ) );
        break;
      }
      case QVariant::Int:
        value = QVariant( OGR_F_GetFieldAsInteger( ogrFet, attIndex ) );
        break;
      case QVariant::LongLong:
        value = QVariant( OGR_F_GetFieldAsInteger64( ogrFet, attIndex ) );
        break;
      case QVariant::Double:
        value = QVariant( OGR_F_GetFieldAsDouble( ogrFet, attIndex ) );
        break;
      case QVariant::Date:
      case QVariant::DateTime:
      case QVariant::Time:
      {
        int year, month, day, hour, minute, second, tzf;

        OGR_F_GetFieldAsDateTime( ogrFet, attIndex, &year, &month, &day, &hour, &minute, &second, &tzf );
        if ( fields.at( attIndex ).type() == QVariant::Date )
          value = QDate( year, month, day );
        else if ( fields.at( attIndex ).type() == QVariant::Time )
          value = QTime( hour, minute, second );
        else
          value = QDateTime( QDate( year, month, day ), QTime( hour, minute, second ) );
      }
      break;
      default:
        Q_ASSERT_X( false, "QgsOgrUtils::getOgrFeatureAttribute", "unsupported field type" );
        if ( ok )
          *ok = false;
    }
  }
  else
  {
    value = QVariant( QString::null );
  }

  return value;
}

bool QgsOgrUtils::readOgrFeatureAttributes( OGRFeatureH ogrFet, const QgsFields& fields, QgsFeature& feature, QTextCodec* encoding )
{
  // read all attributes
  feature.initAttributes( fields.count() );
  feature.setFields( fields );

  if ( !ogrFet )
    return false;

  bool ok = false;
  for ( int idx = 0; idx < fields.count(); ++idx )
  {
    QVariant value = getOgrFeatureAttribute( ogrFet, fields, idx, encoding, &ok );
    if ( ok )
    {
      feature.setAttribute( idx, value );
    }
  }
  return true;
}

bool QgsOgrUtils::readOgrFeatureGeometry( OGRFeatureH ogrFet, QgsFeature& feature )
{
  if ( !ogrFet )
    return false;

  OGRGeometryH geom = OGR_F_GetGeometryRef( ogrFet );
  if ( !geom )
    feature.clearGeometry();
  else
    feature.setGeometry( ogrGeometryToQgsGeometry( geom ) );

  return true;
}

QgsGeometry QgsOgrUtils::ogrGeometryToQgsGeometry( OGRGeometryH geom )
{
  if ( !geom )
    return QgsGeometry();

  // get the wkb representation
  int memorySize = OGR_G_WkbSize( geom );
  unsigned char *wkb = new unsigned char[memorySize];
  OGR_G_ExportToWkb( geom, ( OGRwkbByteOrder ) QgsApplication::endian(), wkb );

  QgsGeometry g;
  g.fromWkb( wkb, memorySize );
  return g;
}

QgsFeatureList QgsOgrUtils::stringToFeatureList( const QString& string, const QgsFields& fields, QTextCodec* encoding )
{
  QgsFeatureList features;
  if ( string.isEmpty() )
    return features;

  QString randomFileName = QStringLiteral( "/vsimem/%1" ).arg( QUuid::createUuid().toString() );

  // create memory file system object from string buffer
  QByteArray ba = string.toUtf8();
  VSIFCloseL( VSIFileFromMemBuffer( randomFileName.toUtf8().constData(), reinterpret_cast< GByte* >( ba.data() ),
                                    static_cast< vsi_l_offset >( ba.size() ), FALSE ) );

  OGRDataSourceH hDS = OGROpen( randomFileName.toUtf8().constData(), false, nullptr );
  if ( !hDS )
  {
    VSIUnlink( randomFileName.toUtf8().constData() );
    return features;
  }

  OGRLayerH ogrLayer = OGR_DS_GetLayer( hDS, 0 );
  if ( !ogrLayer )
  {
    OGR_DS_Destroy( hDS );
    VSIUnlink( randomFileName.toUtf8().constData() );
    return features;
  }

  OGRFeatureH oFeat;
  while (( oFeat = OGR_L_GetNextFeature( ogrLayer ) ) )
  {
    QgsFeature feat = readOgrFeature( oFeat, fields, encoding );
    if ( feat.isValid() )
      features << feat;

    OGR_F_Destroy( oFeat );
  }

  OGR_DS_Destroy( hDS );
  VSIUnlink( randomFileName.toUtf8().constData() );

  return features;
}

QgsFields QgsOgrUtils::stringToFields( const QString& string, QTextCodec* encoding )
{
  QgsFields fields;
  if ( string.isEmpty() )
    return fields;

  QString randomFileName = QStringLiteral( "/vsimem/%1" ).arg( QUuid::createUuid().toString() );

  // create memory file system object from buffer
  QByteArray ba = string.toUtf8();
  VSIFCloseL( VSIFileFromMemBuffer( randomFileName.toUtf8().constData(), reinterpret_cast< GByte* >( ba.data() ),
                                    static_cast< vsi_l_offset >( ba.size() ), FALSE ) );

  OGRDataSourceH hDS = OGROpen( randomFileName.toUtf8().constData(), false, nullptr );
  if ( !hDS )
  {
    VSIUnlink( randomFileName.toUtf8().constData() );
    return fields;
  }

  OGRLayerH ogrLayer = OGR_DS_GetLayer( hDS, 0 );
  if ( !ogrLayer )
  {
    OGR_DS_Destroy( hDS );
    VSIUnlink( randomFileName.toUtf8().constData() );
    return fields;
  }

  OGRFeatureH oFeat;
  //read in the first feature only
  if (( oFeat = OGR_L_GetNextFeature( ogrLayer ) ) )
  {
    fields = readOgrFields( oFeat, encoding );
    OGR_F_Destroy( oFeat );
  }

  OGR_DS_Destroy( hDS );
  VSIUnlink( randomFileName.toUtf8().constData() );
  return fields;
}
