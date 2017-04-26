/***************************************************************************
    qgsvectorlayerfeatureiterator.h
    ---------------------
    begin                : Dezember 2012
    copyright            : (C) 2012 by Martin Dobias
    email                : wonder dot sk at gmail dot com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
#ifndef QGSVECTORLAYERFEATUREITERATOR_H
#define QGSVECTORLAYERFEATUREITERATOR_H

#include "qgis_core.h"
#include "qgsfeatureiterator.h"
#include "qgsfields.h"
#include "qgscoordinatereferencesystem.h"

#include <QSet>
#include <memory>

typedef QMap<QgsFeatureId, QgsFeature> QgsFeatureMap;

class QgsExpressionFieldBuffer;
class QgsVectorLayer;
class QgsVectorLayerEditBuffer;
class QgsVectorLayerJoinBuffer;
class QgsVectorLayerJoinInfo;
class QgsExpressionContext;

class QgsVectorLayerFeatureIterator;

/** \ingroup core
 * Partial snapshot of vector layer's state (only the members necessary for access to features)
*/
class CORE_EXPORT QgsVectorLayerFeatureSource : public QgsAbstractFeatureSource
{
  public:

    /** Constructor for QgsVectorLayerFeatureSource.
     * \param layer source layer
     */
    explicit QgsVectorLayerFeatureSource( const QgsVectorLayer *layer );

    ~QgsVectorLayerFeatureSource();

    virtual QgsFeatureIterator getFeatures( const QgsFeatureRequest &request = QgsFeatureRequest() ) override;

    friend class QgsVectorLayerFeatureIterator;

  protected:

    QgsAbstractFeatureSource *mProviderFeatureSource = nullptr;

    QgsVectorLayerJoinBuffer *mJoinBuffer = nullptr;

    QgsExpressionFieldBuffer *mExpressionFieldBuffer = nullptr;

    QgsFields mFields;

    bool mHasEditBuffer;

    // A deep-copy is only performed, if the original maps change
    // see here https://github.com/qgis/Quantum-GIS/pull/673
    // for explanation
    QgsFeatureMap mAddedFeatures;
    QgsGeometryMap mChangedGeometries;
    QgsFeatureIds mDeletedFeatureIds;
    QList<QgsField> mAddedAttributes;
    QgsChangedAttributesMap mChangedAttributeValues;
    QgsAttributeList mDeletedAttributeIds;

    QgsCoordinateReferenceSystem mCrs;
};

/** \ingroup core
 */
class CORE_EXPORT QgsVectorLayerFeatureIterator : public QgsAbstractFeatureIteratorFromSource<QgsVectorLayerFeatureSource>
{
  public:
    QgsVectorLayerFeatureIterator( QgsVectorLayerFeatureSource *source, bool ownSource, const QgsFeatureRequest &request );

    ~QgsVectorLayerFeatureIterator();

    //! reset the iterator to the starting position
    virtual bool rewind() override;

    //! end of iterating: free the resources / lock
    virtual bool close() override;

    virtual void setInterruptionChecker( QgsInterruptionChecker *interruptionChecker ) override;

  protected:
    //! fetch next feature, return true on success
    virtual bool fetchFeature( QgsFeature &feature ) override;

    //! Overrides default method as we only need to filter features in the edit buffer
    //! while for others filtering is left to the provider implementation.
    virtual bool nextFeatureFilterExpression( QgsFeature &f ) override { return fetchFeature( f ); }

    //! Setup the simplification of geometries to fetch using the specified simplify method
    virtual bool prepareSimplification( const QgsSimplifyMethod &simplifyMethod ) override;

    //! \note not available in Python bindings
    void rewindEditBuffer();

    //! \note not available in Python bindings
    void prepareJoin( int fieldIdx );

    //! \note not available in Python bindings
    void prepareExpression( int fieldIdx );

    //! \note not available in Python bindings
    void prepareFields();

    //! \note not available in Python bindings
    void prepareField( int fieldIdx );

    //! \note not available in Python bindings
    bool fetchNextAddedFeature( QgsFeature &f );
    //! \note not available in Python bindings
    bool fetchNextChangedGeomFeature( QgsFeature &f );
    //! \note not available in Python bindings
    bool fetchNextChangedAttributeFeature( QgsFeature &f );
    //! \note not available in Python bindings
    void useAddedFeature( const QgsFeature &src, QgsFeature &f );
    //! \note not available in Python bindings
    void useChangedAttributeFeature( QgsFeatureId fid, const QgsGeometry &geom, QgsFeature &f );
    //! \note not available in Python bindings
    bool nextFeatureFid( QgsFeature &f );
    //! \note not available in Python bindings
    void addJoinedAttributes( QgsFeature &f );

    /**
     * Adds attributes that don't source from the provider but are added inside QGIS
     * Includes
     *  - Joined fields
     *  - Expression fields
     *
     * \param f The feature will be modified
     * \note not available in Python bindings
     */
    void addVirtualAttributes( QgsFeature &f );

    /** Adds an expression based attribute to a feature
     * \param f feature
     * \param attrIndex attribute index
     * \since QGIS 2.14
     * \note not available in Python bindings
     */
    void addExpressionAttribute( QgsFeature &f, int attrIndex );

    /** Update feature with uncommitted attribute updates.
     * \note not available in Python bindings
     */
    void updateChangedAttributes( QgsFeature &f );

    /** Update feature with uncommitted geometry updates.
     * \note not available in Python bindings
     */
    void updateFeatureGeometry( QgsFeature &f );

    /** Join information prepared for fast attribute id mapping in QgsVectorLayerJoinBuffer::updateFeatureAttributes().
     * Created in the select() method of QgsVectorLayerJoinBuffer for the joins that contain fetched attributes
     */
    struct FetchJoinInfo
    {
      const QgsVectorLayerJoinInfo *joinInfo;//!< Canonical source of information about the join
      QgsAttributeList attributes;      //!< Attributes to fetch
      int indexOffset;                  //!< At what position the joined fields start
      QgsVectorLayer *joinLayer;        //!< Resolved pointer to the joined layer
      int targetField;                  //!< Index of field (of this layer) that drives the join
      int joinField;                    //!< Index of field (of the joined layer) must have equal value

      void addJoinedAttributesCached( QgsFeature &f, const QVariant &joinValue ) const;
      void addJoinedAttributesDirect( QgsFeature &f, const QVariant &joinValue ) const;
    };

    QgsFeatureRequest mProviderRequest;
    QgsFeatureIterator mProviderIterator;
    QgsFeatureRequest mChangedFeaturesRequest;
    QgsFeatureIterator mChangedFeaturesIterator;

    // only related to editing
    QSet<QgsFeatureId> mFetchConsidered;
    QgsGeometryMap::ConstIterator mFetchChangedGeomIt;
    QgsFeatureMap::ConstIterator mFetchAddedFeaturesIt;

    bool mFetchedFid; // when iterating by FID: indicator whether it has been fetched yet or not

    /** Information about joins used in the current select() statement.
      Allows faster mapping of attribute ids compared to mVectorJoins */
    QMap<const QgsVectorLayerJoinInfo *, FetchJoinInfo> mFetchJoinInfo;

    QMap<int, QgsExpression *> mExpressionFieldInfo;

    bool mHasVirtualAttributes;

  private:
    std::unique_ptr<QgsExpressionContext> mExpressionContext;

    QgsInterruptionChecker *mInterruptionChecker = nullptr;

    QList< int > mPreparedFields;
    QList< int > mFieldsToPrepare;

    //! Join list sorted by dependency
    QList< FetchJoinInfo > mOrderedJoinInfoList;

    /**
     * Will always return true. We assume that ordering has been done on provider level already.
     *
     */
    bool prepareOrderBy( const QList<QgsFeatureRequest::OrderByClause> &orderBys ) override;

    //! returns whether the iterator supports simplify geometries on provider side
    virtual bool providerCanSimplify( QgsSimplifyMethod::MethodType methodType ) const override;

    void createOrderedJoinList();

    /**
     * Performs any feature based validity checking, e.g. checking for geometry validity.
     */
    bool testFeature( const QgsFeature &feature );

    /**
     * Checks a feature's geometry for validity, if requested in feature request.
     */
    bool checkGeometryValidity( const QgsFeature &feature );
};

#endif // QGSVECTORLAYERFEATUREITERATOR_H
