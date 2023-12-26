set(VCPKG_POLICY_EMPTY_INCLUDE_FOLDER enabled)

set(PY_PACKAGE_NAME "ply")
string(SUBSTRING "${PY_PACKAGE_NAME}" 0 1 PY_PACKAGE_PREFIX)

vcpkg_download_distfile(ARCHIVE
    URLS "https://files.pythonhosted.org/packages/source/${PY_PACKAGE_PREFIX}/${PY_PACKAGE_NAME}/${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    FILENAME "${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    SHA512 37e39a4f930874933223be58a3da7f259e155b75135f1edd47069b3b40e5e96af883ebf1c8a1bbd32f914a9e92cfc12e29fec05cf61b518f46c1d37421b20008
)

# Might need https://git.alpinelinux.org/aports/tree/main/py3-ply/no-py3-six.patch
vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE ${ARCHIVE}
)

file(GLOB python_versioned LIST_DIRECTORIES true RELATIVE "${CURRENT_INSTALLED_DIR}/lib/" "${CURRENT_INSTALLED_DIR}/lib/python*")
message(STATUS "Building for ${python_versioned}")

set(PYTHON3 "${CURRENT_INSTALLED_DIR}/tools/python3/${python_versioned}")

x_vcpkg_get_python_packages(
    PYTHON_VERSION 3
    PYTHON_EXECUTABLE ${PYTHON3}
    PACKAGES gpep517 flit wheel
    OUT_PYTHON_VAR PYTHON3_FOR_BUILD
)

# Hack ahead: PYTHON3_FOR_BUILD points to the original python binary, not the one in venv (why?)
# set(PYTHON3_VENV "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv")
# set(PYTHON3_FOR_BUILD "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv/bin/${python_versioned}")
# 
# 
# message(STATUS "Using venv at ${PYTHON3_FOR_BUILD}")

vcpkg_execute_required_process(
	COMMAND "${PYTHON3}" "setup.py" "build"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "build-${TARGET_TRIPLET}"
    )

vcpkg_execute_required_process(
	COMMAND "${PYTHON3}" "setup.py" "install" "--root" "${CURRENT_PACKAGES_DIR}" "--prefix=" "--skip-build"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "install-${TARGET_TRIPLET}"
    )

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
