set(PYTHON3 "${CURRENT_INSTALLED_DIR}/tools/python3/python3.11")

set(WORKING_DIR "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-rel/")
execute_process(
	COMMAND mkdir -p "${WORKING_DIR}/"
)

message(STATUS "Running pip install...")
# TODO: this is a bad idea as it installs directly into the install directory
message(STATUS "Bootstrap pip...")
vcpkg_execute_required_process(
	COMMAND "${PYTHON3}" "-m" "ensurepip" "--root" "${CURRENT_PACKAGES_DIR}/lib/python3.11/site-packages"
	WORKING_DIRECTORY "${WORKING_DIR}"
        LOGNAME "ensurepip-${TARGET_TRIPLET}"
)
