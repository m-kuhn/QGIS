set(PYTHON3 "${CURRENT_INSTALLED_DIR}/tools/python3/python3.11")

set(WORKING_DIR "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel/")
execute_process(
	COMMAND mkdir -p "${WORKING_DIR}/"
)

message(STATUS "Bootstrap pip...")
vcpkg_execute_required_process(
	COMMAND "${PYTHON3}" "-m" "ensurepip" "--root" "${WORKING_DIR}/root"
	WORKING_DIRECTORY "${WORKING_DIR}"
        LOGNAME "ensurepip-${TARGET_TRIPLET}"
)

# ensurepip will always append the installed dir to the root, that's not exactly what we want
file(RENAME "${WORKING_DIR}root${CURRENT_INSTALLED_DIR}/bin" "${CURRENT_PACKAGES_DIR}/bin")
file(RENAME "${WORKING_DIR}root${CURRENT_INSTALLED_DIR}/lib" "${CURRENT_PACKAGES_DIR}/lib")
