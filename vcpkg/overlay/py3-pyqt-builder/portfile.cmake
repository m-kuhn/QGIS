set(VCPKG_POLICY_EMPTY_INCLUDE_FOLDER enabled)

set(PY_PACKAGE_NAME "PyQt-builder")
string(SUBSTRING "${PY_PACKAGE_NAME}" 0 1 PY_PACKAGE_PREFIX)

vcpkg_download_distfile(ARCHIVE
    URLS "https://files.pythonhosted.org/packages/source/${PY_PACKAGE_PREFIX}/${PY_PACKAGE_NAME}/${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    FILENAME "${PY_PACKAGE_NAME}-${VERSION}.tar.gz"
    SHA512 ec0b9f7784a32af744111615b93f98d73f284bb752fd71359c798d3b093a01925823effea72c866a5f49f77e3dfc5dee4125bbb289f647d84000bf34b5db6931
)

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
    PACKAGES gpep517 wheel
    OUT_PYTHON_VAR PYTHON3_FOR_BUILD
)

# Hack ahead: PYTHON3_FOR_BUILD points to the original python binary, not the one in venv (why?)
set(PYTHON3_VENV "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv")
set(PYTHON3_FOR_BUILD "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-venv/bin/${python_versioned}")


message(STATUS "Using venv at ${PYTHON3_FOR_BUILD}")

vcpkg_execute_required_process(
	COMMAND "${PYTHON3_VENV}/bin/gpep517" "build-wheel" "--wheel-dir" ".dist" "--output-fd" "2"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "build-${TARGET_TRIPLET}"
    )

file(GLOB python_wheel RELATIVE "${SOURCE_PATH}" "${SOURCE_PATH}/.dist/*.whl")
message(STATUS "found ${python_wheel} in ${SOURCE_PATH}")
vcpkg_execute_required_process(
	COMMAND "${PYTHON3_FOR_BUILD}" "-m" "installer" "-d" "${CURRENT_PACKAGES_DIR}" "-p" "/" "${python_wheel}"
        WORKING_DIRECTORY "${SOURCE_PATH}"
        LOGNAME "install-${TARGET_TRIPLET}"
    )

file(REMOVE_RECURSE ${CURRENT_PACKAGES_DIR}/lib/${python_versioned}/site-packages/pyqtbuild/bundle/dlls/)

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
