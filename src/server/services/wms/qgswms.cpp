/***************************************************************************
                              qgswms.cpp
                              -------------------------
  begin                : December 20 , 2016
  copyright            : (C) 2007 by Marco Hugentobler  ( parts fron qgswmshandler)
                         (C) 2014 by Alessandro Pasotti ( parts from qgswmshandler)
                         (C) 2016 by David Marteau
  email                : marco dot hugentobler at karto dot baug dot ethz dot ch
                         a dot pasotti at itopen dot it
                         david dot marteau at 3liz dot com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include "qgsmodule.h"
#include "qgswmsutils.h"
#include "qgsdxfwriter.h"
#include "qgswmsgetcapabilities.h"
#include "qgswmsgetmap.h"
#include "qgswmsgetstyle.h"
#include "qgswmsgetstyles.h"
#include "qgswmsgetcontext.h"
#include "qgswmsgetschemaextension.h"
#include "qgswmsgetprint.h"
#include "qgswmsgetfeatureinfo.h"
#include "qgswmsdescribelayer.h"
#include "qgswmsgetlegendgraphics.h"

#define QSTR_COMPARE( str, lit )\
  (str.compare( QStringLiteral( lit ), Qt::CaseInsensitive ) == 0)

namespace QgsWms
{

  class Service: public QgsService
  {
    public:
      // Constructor
      Service( const QString& version, QgsServerInterface* serverIface )
          : mVersion( version )
          , mServerIface( serverIface )
      {}

      QString name()    const { return QStringLiteral( "WMS" ); }
      QString version() const { return mVersion; }

      bool allowMethod( QgsServerRequest::Method method ) const
      {
        return method == QgsServerRequest::GetMethod;
      }

      void executeRequest( const QgsServerRequest& request, QgsServerResponse& response,
                           QgsProject* project )
      {
        Q_UNUSED( project );

        QgsServerRequest::Parameters params = request.parameters();
        QString versionString = params.value( "VERSION" );
        if ( versionString.isEmpty() )
        {
          //WMTVER needs to be supported by WMS 1.1.1 for backwards compatibility with WMS 1.0.0
          versionString = params.value( "WMTVER" );
        }

        // Set the default version
        if ( versionString.isEmpty() )
        {
          versionString = mVersion;
        }

        // Get the request
        QString req = params.value( QStringLiteral( "REQUEST" ) );
        if ( req.isEmpty() )
        {
          writeError( response, QStringLiteral( "OperationNotSupported" ),
                      QStringLiteral( "Please check the value of the REQUEST parameter" ) );
          return;
        }

        if (( QSTR_COMPARE( mVersion, "1.1.1" ) && QSTR_COMPARE( req, "capabilities" ) )
            || QSTR_COMPARE( req, "GetCapabilities" ) )
        {
          writeGetCapabilities( mServerIface, versionString, request, response, false );
        }
        else if QSTR_COMPARE( req, "GetProjectSettings" )
        {
          //getProjectSettings extends WMS 1.3.0 capabilities
          versionString = QStringLiteral( "1.3.0" );
          writeGetCapabilities( mServerIface, versionString, request, response, true );
        }
        else if QSTR_COMPARE( req, "GetMap" )
        {
          QString format = params.value( QStringLiteral( "FORMAT" ) );
          if QSTR_COMPARE( format, "application/dxf" )
          {
            writeAsDxf( mServerIface, versionString, request, response );
          }
          else
          {
            writeGetMap( mServerIface, versionString, request, response );
          }
        }
        else if QSTR_COMPARE( req, "GetFeatureInfo" )
        {
          writeGetFeatureInfo( mServerIface, versionString, request, response );
        }
        else if QSTR_COMPARE( req, "GetContext" )
        {
          writeGetContext( mServerIface, versionString, request, response );
        }
        else if QSTR_COMPARE( req, "GetSchemaExtension" )
        {
          writeGetSchemaExtension( mServerIface, versionString, request, response );
        }
        else if QSTR_COMPARE( req, "GetStyle" )
        {
          writeGetStyle( mServerIface, versionString, request, response );
        }
        else if QSTR_COMPARE( req, "GetStyles" )
        {
          writeGetStyles( mServerIface, versionString, request, response );
        }
        else if QSTR_COMPARE( req, "DescribeLayer" )
        {
          writeDescribeLayer( mServerIface, versionString, request, response );
        }
        else if ( QSTR_COMPARE( req, "GetLegendGraphic" ) || QSTR_COMPARE( req, "GetLegendGraphics" ) )
        {
          writeGetLegendGraphics( mServerIface, versionString, request, response );
        }
        else if QSTR_COMPARE( req, "GetPrint" )
        {
          writeGetPrint( mServerIface, versionString, request, response );
        }
        else
        {
          // Operation not supported
          writeError( response, QStringLiteral( "OperationNotSupported" ),
                      QString( "Request %1 is not supported" ).arg( req ) );
          return;
        }
      }

    private:
      QString mVersion;
      QgsServerInterface* mServerIface;
  };


} // namespace QgsWms


// Module
class QgsWmsModule: public QgsServiceModule
{
  public:
    void registerSelf( QgsServiceRegistry& registry, QgsServerInterface* serverIface )
    {
      QgsDebugMsg( "WMSModule::registerSelf called" );
      registry.registerService( new  QgsWms::Service( "1.3.0", serverIface ) );
    }
};


// Entry points
QGISEXTERN QgsServiceModule* QGS_ServiceModule_Init()
{
  static QgsWmsModule module;
  return &module;
}
QGISEXTERN void QGS_ServiceModule_Exit( QgsServiceModule* )
{
  // Nothing to do
}





