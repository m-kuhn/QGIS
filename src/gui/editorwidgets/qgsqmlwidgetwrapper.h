/***************************************************************************
  qgsqmlwidgetwrapper.h

 ---------------------
 begin                : 25.6.2018
 copyright            : (C) 2018 by Matthias Kuhn
 email                : matthias@opengis.ch
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
#ifndef QGSQMLWIDGETWRAPPER_H
#define QGSQMLWIDGETWRAPPER_H

#include "qgswidgetwrapper.h"
#include "qgis.h"
#include "qgis_gui.h"


class GUI_EXPORT QgsQmlWidgetWrapper : public QgsWidgetWrapper
{
    Q_OBJECT

  public:
    QgsQmlWidgetWrapper( QgsVectorLayer *layer, QWidget *editor, QWidget *parent );

    bool valid() const override;

    QWidget *createWidget( QWidget *parent ) override;

    void initWidget( QWidget *editor ) override;

  public slots:

    void setFeature( const QgsFeature &feature ) override;

  private:
    QTemporaryFile mQmlFile;
};

#endif // QGSQMLWIDGETWRAPPER_H
