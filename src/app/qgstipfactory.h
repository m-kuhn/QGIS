/***************************************************************************
    qgstipfactory.h
    ---------------------
    begin                : February 2011
    copyright            : (C) 2011 by Tim Sutton
    email                : tim at linfiniti dot com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#ifndef QGSTIPFACTORY
#define QGSTIPFACTORY

#include "qgstip.h"
#include <QList>
#include "qgis_app.h"

/** \ingroup app
* \brief A factory class to serve up tips to the user.
* Tips can be generic, in which case they make no mention of
* gui dialogs etc, or gui-specific in which case they may allude
* to features of the graphical user interface.
* \see also QgsTipOfTheDay, QgsTip
*/

class APP_EXPORT QgsTipFactory : QObject
{
    Q_OBJECT
  public:
    //! Constructor
    QgsTipFactory();

    ~QgsTipFactory();

    /** Get a random tip (generic or gui-centric)
     * \returns An QgsTip containing the tip
     */
    QgsTip getTip();

    /** Get a specific tip (generic or gui-centric).
     * \param position The tip returned will be based on the
     *        number passed in as position. If the
     *        position is invalid, an empty string will be
     *        returned.
     * \returns An QgsTip containing the tip
     */
    QgsTip getTip( int position );

    /** Get a random generic tip
     * \returns An QgsTip containing the tip
     */
    QgsTip getGenericTip();

    /** Get a random gui-centric tip
     * \returns An QgsTip  containing the tip
     */
    QgsTip getGuiTip();

    int position( QgsTip );
    int count();

  private:
    void addGenericTip( const QgsTip & );
    void addGuiTip( const QgsTip & );
    int randomNumber( int max );
    //@TODO move tipts into a sqlite db
    QList <QgsTip> mGenericTips;
    QList <QgsTip> mGuiTips;
    QList <QgsTip> mAllTips;
};
#endif //QGSTIPFACTORY

