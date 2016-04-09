mkdir build
cd build

ln -s ${HOME}/osgeo4travis/bin/ccache ${HOME}/osgeo4travis/bin/clang++-3.6
ln -s ${HOME}/osgeo4travis/bin/ccache ${HOME}/osgeo4travis/bin/clang-3.6

ccache -s

export CXX="clang++-3.6"
export CC="clang-3.6"
export PATH=${HOME}/osgeo4travis/bin:${PATH}
export PYTHONPATH=${HOME}/osgeo4travis/lib/python3.3/site-packages/

cmake --version
${CC} --version
${CXX} --version

CLANG_WARNINGS="-Wimplicit-fallthrough"

# Include this line for debug reasons
#      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
#
cmake \
      -DCMAKE_PREFIX_PATH=/home/travis/osgeo4travis \
      -DWITH_STAGED_PLUGINS=ON \
      -DWITH_GRASS=ON \
      -DSUPPRESS_QT_WARNINGS=ON \
      -DENABLE_MODELTEST=ON \
      -DENABLE_PGTEST=ON \
      -DWITH_QSPATIALITE=ON \
      -DWITH_QWTPOLAR=OFF \
      -DWITH_QTWEBKIT=OFF \
      -DWITH_APIDOC=ON \
      -DWITH_ASTYLE=ON \
      -DWITH_SERVER=ON \
      -DENABLE_QT5=ON \
      -DENABLE_PYTHON3=ON \
      -DCXX_EXTRA_FLAGS="$CLANG_WARNINGS" \
      ..
