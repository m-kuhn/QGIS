vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO hobuinc/untwine
    REF "${VERSION}"
    SHA512 47899fb15baaded2f244014309381d62b9b0c1e5b19aca0ed6123b35407fcabfb715bc4c2383d5d1768fa451ea8f2ad9e1b4e0a1376fe1969b0cd5773a88f578
    HEAD_REF master
    PATCHES
      install_qgis_api.patch
)

vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
)
vcpkg_cmake_install()

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
