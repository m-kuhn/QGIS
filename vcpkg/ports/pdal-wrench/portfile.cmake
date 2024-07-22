vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO PDAL/wrench
    REF "v${VERSION}"
    SHA512 efa7992d28de49d70c24b29f87eeadb9f9638b58b8266c7f9e7a211a3e13ebed88b7d3b9c4028c582741d30224aaa5c5a37b075e33588a1de62ace8b05f6e5d2
    HEAD_REF master
)

vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
)
vcpkg_cmake_install()

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
