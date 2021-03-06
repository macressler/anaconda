# - Find vorbis
# Find the native vorbis includes and libraries
#
#  VORBIS_INCLUDE_DIR - where to find vorbis.h, etc.
#  VORBIS_LIBRARIES   - List of libraries when using vorbis(file).
#  VORBIS_FOUND       - True if vorbis found.

find_path(OGG_INCLUDE_DIR ogg/ogg.h)
find_path(VORBIS_INCLUDE_DIR vorbis/vorbisfile.h)
find_library(OGG_LIBRARY NAMES libogg_static libogg ogg_static ogg)
find_library(VORBIS_LIBRARY NAMES 
    libvorbis_static libvorbis vorbis_static vorbis)
find_library(VORBISFILE_LIBRARY NAMES 
    libvorbisfile_static libvorbisfile vorbisfile vorbisfile_static)
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(VORBIS DEFAULT_MSG
    OGG_INCLUDE_DIR VORBIS_INCLUDE_DIR
    OGG_LIBRARY VORBIS_LIBRARY VORBISFILE_LIBRARY)
    
if(VORBIS_FOUND)
    set(VORBIS_LIBRARIES ${VORBISFILE_LIBRARY} ${VORBIS_LIBRARY}
        ${OGG_LIBRARY})
else(VORBIS_FOUND)
    set(VORBIS_LIBRARIES)
endif(VORBIS_FOUND)

mark_as_advanced(OGG_INCLUDE_DIR VORBIS_INCLUDE_DIR)
mark_as_advanced(OGG_LIBRARY VORBIS_LIBRARY VORBISFILE_LIBRARY)
