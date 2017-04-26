/***************************************************************************
        qgstipfactory.cpp
        ---------------------
    begin                : February 2011
    copyright            : (C) 2007 by Tim Sutton
    email                : tim at linfiniti dot com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include "qgstipfactory.h"
#include <QTime>
//for rand & srand
#include <cstdlib>


QgsTipFactory::QgsTipFactory() : QObject()
{
  // I'm just doing this in a simple way so
  // its easy for translators...later
  // it its worth the time I'll move this data
  // into a sqlite database...
  QgsTip myTip;
  myTip.setTitle( tr( "QGIS is open source" ) );
  myTip.setContent( tr( "QGIS is open source software."
                        " This means that the software source code can be freely viewed"
                        " and modified. The GPL places a restriction that any modifications"
                        " you make must be made available in source form to whoever you give"
                        " modified versions to, and that you can not create a new version of"
                        " QGIS under a 'closed source' license. Visit"
                        " <a href=\"https://qgis.org\"> the QGIS home page</a>"
                        " for more information."
                      ) );
  addGenericTip( myTip );
  //
  myTip.setTitle( tr( "QGIS Publications" ) );
  myTip.setContent( tr( "If you write a scientific paper or any other article"
                        " that refers to QGIS we would love to include your work"
                        " in the <a href=\"https://qgis.org/en/site/about/case_studies/index.html\">case studies section</a> of"
                        " the QGIS home page."
                      ) );
  addGenericTip( myTip );
  myTip.setTitle( tr( "Become a QGIS translator" ) );
  myTip.setContent( tr( "Would you like to see QGIS"
                        " in your native language? We are looking for more translators"
                        " and would appreciate your help! The translation process is"
                        " fairly straight forward - instructions are available in the"
                        " QGIS wiki"
                        " <a href=\"https://qgis.org/en/site/getinvolved/translate.html#howto-translate-gui\">translator's page.</a>"
                      ) );
  addGuiTip( myTip );
  myTip.setTitle( tr( "Getting Help With QGIS" ) );
  myTip.setContent( tr( "If you need help using QGIS"
                        " there is a 'users' mailing list where users help each other with issues"
                        " related to using QGIS. We also have a 'developers' mailing list"
                        " for those wanting help and discuss things relating to the QGIS code base."
                        " Details on different means to get help are described in the"
                        " <a href=\"https://qgis.org/en/site/forusers/support.html#mailing-lists\">community section</a> of the QGIS home page."
                      ) );
  addGuiTip( myTip );
  myTip.setTitle( tr( "Is it 'QGIS' or 'Quantum GIS'?" ) );
  myTip.setContent( tr( "Both used to be correct, but we recently decided to just use 'QGIS'. For articles we suggest you write 'QGIS is ....'"
                      ) );
  addGenericTip( myTip );
  myTip.setTitle( tr( "How do I refer to QGIS?" ) );
  myTip.setContent( tr( "QGIS is spelled in all caps."
                        " We have various subprojects of the QGIS project"
                        " and it will help to avoid confusion if you refer to each by"
                        " its name:"
                        "<ul>"
                        "<li><strong>QGIS Desktop</strong> - this is the desktop application that you know and love so much :-).</li>"
                        "<li><strong>QGIS Library</strong> - this is the C++ library that contains"
                        " the core logic that is used to build the QGIS user interface and other applications.</li>"
                        "<li><strong>QGIS Server</strong> - this is a server-side application based on the QGIS Library"
                        " that will serve up your .qgs projects using OGC standard protocols.</li>"
                        "</ul>"
                      ) );
  addGenericTip( myTip );
  // This tip contributed by Andreas Neumann
  myTip.setTitle( tr( "Add the current date to a map layout" ) );
  myTip.setContent( tr( "You can add a current date variable to your map"
                        " layout. Create a regular text label and add the string"
                        " $CURRENT_DATE(yyyy-MM-dd) to the text box. See the"
                        " <a href=\"https://doc.qt.io/qt-5.3/qdate.html#toString\">"
                        "QDate::toString format documentation</a> for the possible date formats."
                      ) );
  addGuiTip( myTip );
  myTip.setTitle( tr( "Moving Elements and Maps in the Print Composer" ) );
  myTip.setContent( tr( "In the print composer toolbar you can find two buttons for moving"
                        " elements. The first one ( <img src=\":/images/themes/default/mActionSelect.svg\"/> )"
                        " selects and moves elements in the layout. After selecting the element"
                        " with this tool you can also move them around with the arrow keys."
                        " For accurate positioning use the <strong>%1</strong> section,"
                        " which can be found in the tab <strong>%2</strong>."
                        " The other move tool ( <img src=\":/images/themes/default/mActionMoveItemContent.svg\"/> )"
                        " allows you to move the map content within a map frame." )
                    .arg( tr( "Position and Size" ) )
                    .arg( tr( "Item Properties" ) )
                  );
  addGuiTip( myTip );
  addGuiTip( myTip );
  // This  tip contributed by Andreas Neumann
  myTip.setTitle( tr( "Lock an item in the layout view" ) );
  myTip.setContent( tr( "Locking an element in the layout view prevents you to select or accidentally"
                        " move it with the mouse. Locking an item is done by checking its"
                        " <img src=\":/images/themes/default/locked.svg\"/> state in the"
                        " <strong>%1</strong> tab. While in a locked state, you can still get it"
                        " selected from the <strong>%1</strong> tab, and configure any of its"
                        " properties in the <strong>%2</strong> tab, including precisely setting"
                        " its position and size." )
                    .arg( tr( "Items" ) )
                    .arg( tr( "Item Properties" ) )
                  );
  addGuiTip( myTip );
  // This  tip contributed by Andreas Neumann
  myTip.setTitle( tr( "Rotating a map and linking a north arrow" ) );
  myTip.setContent( tr( "In the Print Composer you can rotate a map by setting its rotation value"
                        " in the tab <strong>Item Properties -> Map -> Main properties</strong> section."
                        " To place a north arrow in your layout you can use the"
                        " <strong>%1</strong> tool. After the selection and"
                        " placement of the north arrow in the layout you can link it"
                        " with a specific map frame by activating the <strong>%2</strong>"
                        " checkbox and selecting a map frame. Whenever you change the rotation"
                        " value of a linked map, the north arrow will now automatically adjust"
                        " its rotation." )
                    .arg( tr( "Add Image" ) )
                    .arg( tr( "Sync with map" ) )
                  );
  addGuiTip( myTip );
  addGuiTip( myTip );
  // This  tip contributed by Andreas Neumann
  myTip.setTitle( tr( "Numeric scale value in map layout linked to map frame" ) );
  myTip.setContent( tr( "If you want to place a text label as a placeholder for the"
                        " current scale, linked to a map frame, you need to place a scalebar and"
                        " set the style to 'Numeric'. You also need to select the map frame if there"
                        " is more than one."
                      ) );
  addGuiTip( myTip );
  // by Tim
  myTip.setTitle( tr( "Using the mouse scroll wheel" ) );
  myTip.setContent( tr( "You can use the scroll wheel on your mouse to zoom in,"
                        " out and pan the map. Scroll forwards to zoom in, scroll backwards to"
                        " zoom out and press and hold the scroll wheel down to pan the map. You"
                        " can configure the zoom scale factor in the <strong> %1 -> %2 </strong> panel." )
                    .arg( tr( "Options" ) )
                    .arg( tr( "Map tools" ) )
                  );
  addGuiTip( myTip );
  // Tip contributed by Alister Hood
  myTip.setTitle( tr( "Join intersected polylines when rendering" ) );
  myTip.setContent( tr( "When applying layered styles to a polyline layer, you can join"
                        " intersecting lines together simply by enabling symbol levels."
                        " The image below shows a before (left) and after (right) view of"
                        " an intersection when symbol levels are enabled." ) +
                    QStringLiteral( "<p><center><img src=\":/images/tips/symbol_levels.png\"/></center></p>" )
                  );
  addGuiTip( myTip );
  // by Tim
  myTip.setTitle( tr( "Auto-enable your favorite coordinate reference system (CRS)" ) );
  myTip.setContent( tr( "In the <strong>options</strong> dialog, under the <strong>CRS</strong> tab,"
                        " you can configure QGIS so that whenever you create a new project"
                        " your favorite CRS is predefined automatically."
                      ) );
  addGuiTip( myTip );
  // by Tim
  myTip.setTitle( tr( "Sponsor QGIS" ) );
  myTip.setContent( tr( "If QGIS is saving you money or you like our work and"
                        " have the financial ability to help, please consider sponsoring the"
                        " development of QGIS. We use money from sponsors to pay for"
                        " travel and costs related to our regular hackfest meetings and invest it into"
                        " stability enhancements and infrastructure maintenance expenses. Please see the <a"
                        " href=\"https://qgis.org/en/site/getinvolved/governance/sponsorship/sponsorship.html\">QGIS Sponsorship Web"
                        " Page</a> for more details."
                      ) );
  addGenericTip( myTip );
  // by gsherman
  myTip.setTitle( tr( "QGIS has Plugins!" ) );
  myTip.setContent( tr( "QGIS has plugins that extend its functionality."
                        " QGIS ships with some core plugins which you can explore from the"
                        " <strong> %1 -> %2</strong> menu. In addition there"
                        " are a lot of <a href=\"https://plugins.qgis.org/\">Python plugins</a>"
                        " contributed by the user community that can be"
                        " installed via this same menu. Don't miss out on all QGIS has to offer!"
                        " Check out the plugins and see what they can do for you." )
                    .arg( tr( "Plugins" ) )
                    .arg( tr( "Manage and Install Plugins..." ) )
                  );
  addGuiTip( myTip );
  addGenericTip( myTip );
  // by yjacolin
  myTip.setTitle( tr( "Add an action to a layer" ) );
  myTip.setContent( tr( "Actions on a layer allow users to trigger actions when clicking on a geometry"
                        " with the <strong>Run Feature Action</strong> tool"
                        " or from the feature form."
                        "For example, you can open a HTML page using a field value of the feature "
                        "as a parameter. Look at the <a href=\"https://docs.qgis.org/latest/en/docs/user_manual/working_with_vector/vector_properties.html?#actions-menu\">documentation</a>."
                      ) );
  addGuiTip( myTip );
  // by yjacolin
  myTip.setTitle( tr( "Copy, paste and cut in QGIS" ) );
  myTip.setContent( tr( "Copy, paste, and cut work as in another applications in QGIS. Select a "
                        "feature (a geometry or an attribute row in the attribute table) and use "
                        "one of these shortcuts: Ctrl+C to copy, Ctrl+X to cut, and Ctrl+V to paste."
                      ) );
  addGuiTip( myTip );
  // by yjacolin
  myTip.setTitle( tr( "Right click with identify tools" ) );
  myTip.setContent( tr( "Right click with the identify tool to show a context menu from which you can "
                        "choose the layer in which to identify a feature. A sub-menu will list features "
                        "identified and a third sub-menu will show the action link setup for the layer. "
                        "If one of this sub-menu doesn't contain any information, the next sub-menu "
                        "will appear instead. For example, if you have just one layer, and click "
                        "somewhere with several features, the first menu will list the features "
                        "instead of layer list."
                      ) );
  addGuiTip( myTip );
  // by Alister Hood
  myTip.setTitle( tr( "Use VRT files" ) );
  myTip.setContent( tr( "If you have a number of aerial photos spread across a wide area, instead of "
                        "loading each file as a separate layer you can treat them all as a single layer "
                        "by using a .vrt file. "
                        "To create a .vrt, go to <strong> %1 -> %2 -> %3</strong>." )
                    .arg( tr( "Raster" ) )
                    .arg( tr( "Miscellaneous" ) )
                    .arg( tr( "Build Virtual Raster (Catalog)" ) )
                  );
  addGuiTip( myTip );
  // by Harrissou Sant-anna
  myTip.setTitle( tr( "Switch quickly between different styles of a layer" ) );
  myTip.setContent( tr( "From the layer properties dialog, use the <strong>Styles -> Add</strong> combobox"
                        " to create as many combinations of layer properties (symbology, labeling,"
                        " diagram, fields form, actions...) as you want. Then, simply switch between styles"
                        " in the context menu of the layer in the <strong>%1</strong>." )
                    .arg( tr( "Layers Panel" ) )
                  );
  addGuiTip( myTip );
  // by Harrissou Sant-anna
  myTip.setTitle( tr( "Live update rendering" ) );
  myTip.setContent( tr( "Press F7 to activate the <strong>%1</strong> panel from which you can"
                        " easily and quickly configure the layer rendering. Check the <strong>%2</strong>"
                        " option to immediately see each of your modifications on the map canvas." )
                    .arg( tr( "Layer Styling" ) )
                    .arg( tr( "Live update" ) )
                  );
  addGuiTip( myTip );
  // by Harrissou Sant-anna
  myTip.setTitle( tr( "Print or export a specific feature from an atlas composition" ) );
  myTip.setContent( tr( "If you want to print or export the composition for only one feature of the atlas,"
                        " start the atlas preview, select the desired feature in the drop-down list"
                        " and click the <strong>Composer -> Print</strong> menu (or use <strong>Composer ->"
                        " Export...</strong> for any supported file format).<br>"
                        "Atlas features can also be selected from the canvas by using the <strong>Run feature action</strong>"
                        " tool 'Set as atlas feature' from the attributes toolbar."
                      ) );
  addGuiTip( myTip );
  // by Harrissou Sant-anna
  myTip.setTitle( tr( "Start QGIS from command line" ) );
  myTip.setContent( tr( "QGIS can be launched from command line and supports a number of options. This can be"
                        " handy if you need to use QGIS with particular configurations such as a custom"
                        " user profile or without plugins... To get the list of the options"
                        " enter <pre>qgis --help</pre> on the command line."
                      ) );
  addGuiTip( myTip );
  // by Harrissou Sant-anna
  myTip.setTitle( tr( "Set your own shortcuts for your actions" ) );
  myTip.setContent( tr( "QGIS provides you with a list of predefined shortcuts you can use to speed"
                        " your workflow. These are available under <strong> %1 -> %2 </strong>"
                        "  menu and can be extended and customized for any dialog or tool." )
                    .arg( tr( "Settings" ) )
                    .arg( tr( "Keyboard Shortcuts" ) )
                  );
  addGuiTip( myTip );

  /* Template for adding more tips
  myTip.setTitle(tr(""));
  myTip.setContent(tr(""
        ));
  addGuiTip(myTip);
  */
}

QgsTipFactory::~QgsTipFactory()
{

}
//private helper method
void QgsTipFactory::addGuiTip( const QgsTip &tip )
{
  mGuiTips << tip;
  mAllTips << tip;
}
//private helper method
void QgsTipFactory::addGenericTip( const QgsTip &tip )
{
  mGenericTips << tip;
  mAllTips << tip;
}
QgsTip QgsTipFactory::getTip()
{
  int myRand = qrand();
  int myValue = static_cast<int>( myRand % mAllTips.count() ); //range [0,(count-1)]
  QgsTip myTip = mAllTips.at( myValue );
  return myTip;
}
QgsTip QgsTipFactory::getTip( int position )
{
  QgsTip myTip = mAllTips.at( position );
  return myTip;
}
QgsTip QgsTipFactory::getGenericTip()
{
  int myRand = qrand();
  int myValue = static_cast<int>( myRand % mGenericTips.count() ); //range [0,(count-1)]
  QgsTip myTip = mGenericTips.at( myValue );
  return myTip;
}
QgsTip QgsTipFactory::getGuiTip()
{
  int myRand = qrand();
  int myValue = static_cast<int>( myRand % mGuiTips.count() ); //range [0,(count-1)]
  QgsTip myTip = mGuiTips.at( myValue );
  return myTip;
}

int QgsTipFactory::randomNumber( int max )
{
  Q_UNUSED( max );
  return 0;
}

int QgsTipFactory::position( QgsTip tip )
{
  for ( int i = 0; i < mAllTips.count(); ++i )
  {
    QgsTip myTip = mAllTips.at( i );
    if ( myTip.title() == tip.title() )
    {
      return i;
    }
  }
  return -1;
}

int QgsTipFactory::count()
{
  return mAllTips.count();
}
