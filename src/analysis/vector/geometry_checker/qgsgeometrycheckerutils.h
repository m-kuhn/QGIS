/***************************************************************************
 *  qgsgeometrycheckerutils.h                                              *
 *  -------------------                                                    *
 *  copyright            : (C) 2014 by Sandro Mani / Sourcepole AG         *
 *  email                : smani@sourcepole.ch                             *
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#ifndef QGS_GEOMETRYCHECKERUTILS_H
#define QGS_GEOMETRYCHECKERUTILS_H

#include "qgis_analysis.h"
#include "qgsfeature.h"
#include "geometry/qgsabstractgeometry.h"
#include "geometry/qgspoint.h"
#include "qgsgeometrycheckcontext.h"
#include <qmath.h>

class QgsGeometryEngine;
class QgsFeaturePool;
class QgsFeedback;

class ANALYSIS_EXPORT QgsGeometryCheckerUtils
{
  public:
    class ANALYSIS_EXPORT LayerFeature
    {
      public:

        /**
         * Create a new layer/feature combination.
         * The layer is defined by \a pool, \a feature needs to be from this layer.
         * If \a useMapCrs is True, geometries will be reprojected to the mapCrs defined
         * in \a context.
         */
        LayerFeature( const QgsFeaturePool *pool, const QgsFeature &feature, const QgsGeometryCheckContext *context, bool useMapCrs );

        /**
         * Returns the feature.
         * The geometry will not be reprojected regardless of useMapCrs.
         */
        const QgsFeature &feature() const;

        /**
         * The layer.
         */
        QPointer<QgsVectorLayer> layer() const SIP_SKIP;

        /**
         * The layer id.
         */
        QString layerId() const;

        /**
         * Returns the geometry of this feature.
         * If useMapCrs was specified, it will already be reprojected into the
         * CRS specified in the context specified in the constructor.
         */
        const QgsGeometry &geometry() const;
        QString id() const;
        bool operator==( const LayerFeature &other ) const;
        bool operator!=( const LayerFeature &other ) const;

        /**
         * Returns if the geometry is reprojected to the map CRS or not.
         */
        bool useMapCrs() const;

      private:
        const QgsFeaturePool *mFeaturePool;
        QgsFeature mFeature;
        QgsGeometry mGeometry;
        bool mMapCrs;
    };

    class ANALYSIS_EXPORT LayerFeatures
    {
      public:
#ifndef SIP_RUN
        LayerFeatures( const QMap<QString, QgsFeaturePool *> &featurePools,
                       const QMap<QString, QgsFeatureIds> &featureIds,
                       const QList<QgsWkbTypes::GeometryType> &geometryTypes,
                       QgsFeedback *feedback,
                       const QgsGeometryCheckContext *context,
                       bool useMapCrs = false );

        LayerFeatures( const QMap<QString, QgsFeaturePool *> &featurePools,
                       const QList<QString> &layerIds, const QgsRectangle &extent,
                       const QList<QgsWkbTypes::GeometryType> &geometryTypes,
                       const QgsGeometryCheckContext *context );

        class iterator
        {
          public:
            iterator( const QList<QString>::const_iterator &layerIt, const LayerFeatures *parent );
            ~iterator();
            const iterator &operator++();
            iterator operator++( int ) { iterator tmp( *this ); ++*this; return tmp; }
            const LayerFeature &operator*() const { Q_ASSERT( mCurrentFeature ); return *mCurrentFeature; }
            bool operator!=( const iterator &other ) { return mLayerIt != other.mLayerIt || mFeatureIt != other.mFeatureIt; }

          private:
            bool nextLayerFeature( bool begin );
            bool nextLayer( bool begin );
            bool nextFeature( bool begin );
            QList<QString>::const_iterator mLayerIt;
            QgsFeatureIds::const_iterator mFeatureIt;
            const LayerFeatures *mParent;
            const LayerFeature *mCurrentFeature = nullptr;
        };

        iterator begin() const { return iterator( mLayerIds.constBegin(), this ); }
        iterator end() const { return iterator( mLayerIds.end(), this ); }

#endif

      private:
#ifdef SIP_RUN
        LayerFeatures();
#endif
        QMap<QString, QgsFeaturePool *> mFeaturePools;
        QMap<QString, QgsFeatureIds> mFeatureIds;
        QList<QString> mLayerIds;
        QgsRectangle mExtent;
        QList<QgsWkbTypes::GeometryType> mGeometryTypes;
        QgsFeedback *mFeedback = nullptr;
        const QgsGeometryCheckContext *mContext = nullptr;
        bool mUseMapCrs = true;
    };

#ifndef SIP_RUN

    static std::unique_ptr<QgsGeometryEngine> createGeomEngine( const QgsAbstractGeometry *geometry, double tolerance );

    static QgsAbstractGeometry *getGeomPart( QgsAbstractGeometry *geom, int partIdx );
    static const QgsAbstractGeometry *getGeomPart( const QgsAbstractGeometry *geom, int partIdx );

    static QList <const QgsLineString *> polygonRings( const QgsPolygon *polygon );

    static void filter1DTypes( QgsAbstractGeometry *geom );

    /**
     * Returns the number of points in a polyline, accounting for duplicate start and end point if the polyline is closed
     * \param polyLine The polyline
     * \returns The number of distinct points of the polyline
     */
    static inline int polyLineSize( const QgsAbstractGeometry *geom, int iPart, int iRing, bool *isClosed = nullptr )
    {
      if ( !geom->isEmpty() )
      {
        int nVerts = geom->vertexCount( iPart, iRing );
        QgsPoint front = geom->vertexAt( QgsVertexId( iPart, iRing, 0 ) );
        QgsPoint back = geom->vertexAt( QgsVertexId( iPart, iRing, nVerts - 1 ) );
        bool closed = back == front;
        if ( isClosed )
          *isClosed = closed;
        return closed ? nVerts - 1 : nVerts;
      }
      else
      {
        if ( isClosed )
          *isClosed = true;
        return 0;
      }
    }

    static bool pointOnLine( const QgsPoint &p, const QgsLineString *line, double tol, bool excludeExtremities = false );

    static QList<QgsPoint> lineIntersections( const QgsLineString *line1, const QgsLineString *line2, double tol );

    static double sharedEdgeLength( const QgsAbstractGeometry *geom1, const QgsAbstractGeometry *geom2, double tol );

    /**
       * \brief Determine whether two points are equal up to the specified tolerance
       * \param p1 The first point
       * \param p2 The second point
       * \param tol The tolerance
       * \returns Whether the points are equal
       */
    static inline bool pointsFuzzyEqual( const QgsPointXY &p1, const QgsPointXY &p2, double tol )
    {
      double dx = p1.x() - p2.x(), dy = p1.y() - p2.y();
      return ( dx * dx + dy * dy ) < tol * tol;
    }

    static inline bool canDeleteVertex( const QgsAbstractGeometry *geom, int iPart, int iRing )
    {
      int nVerts = geom->vertexCount( iPart, iRing );
      QgsPoint front = geom->vertexAt( QgsVertexId( iPart, iRing, 0 ) );
      QgsPoint back = geom->vertexAt( QgsVertexId( iPart, iRing, nVerts - 1 ) );
      bool closed = back == front;
      return closed ? nVerts > 4 : nVerts > 2;
    }

#endif

}; // QgsGeometryCheckerUtils

#endif // QGS_GEOMETRYCHECKERUTILS_H
