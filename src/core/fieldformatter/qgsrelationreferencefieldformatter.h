/***************************************************************************
  qgsrelationreferencefieldformatter.h - QgsRelationReferenceFieldFormatter

 ---------------------
 begin                : 3.12.2016
 copyright            : (C) 2016 by Matthias Kuhn
 email                : matthias@opengis.ch
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
#ifndef QGSRELATIONREFERENCEFIELDKIT_H
#define QGSRELATIONREFERENCEFIELDKIT_H

#include "qgis_core.h"
#include "qgsfieldformatter.h"

/**
 * \ingroup core
 * Field formatter for a relation reference field.
 * A value relation field formatter looks up the values from
 * features on another layer.
 *
 * \note Added in QGIS 3.0
 */
class CORE_EXPORT QgsRelationReferenceFieldFormatter : public QgsFieldFormatter
{
  public:
    virtual QString id() const override;

    virtual QString representValue( QgsVectorLayer* layer, int fieldIndex, const QVariantMap& config, const QVariant& cache, const QVariant& value ) const override;

    virtual QVariant sortValue( QgsVectorLayer *layer, int fieldIndex, const QVariantMap&config, const QVariant& cache, const QVariant& value ) const override;
};

#endif // QGSRELATIONREFERENCEFIELDKIT_H
