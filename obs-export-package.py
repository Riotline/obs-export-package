import obspython as obs # type: ignore
import re, json, unicodedata


SCRIPT_VER = "0.0.1"
suffix = ""
save_location = ""

# OBS Scripting Description
def script_description():
  return f"""<center><h2>Export Package</h2></center>
            <center><p>Version: {SCRIPT_VER}</p></center>
            <p>This plugin assists with creating portable packages
              by organising asset into one folder.</p>"""

def script_defaults(settings):
  obs.obs_data_set_default_string(settings, "export_suffix", "EXPORT")
  obs.obs_data_set_default_string(settings, "export_location", "")

def script_properties():
  props = obs.obs_properties_create()
  obs.obs_properties_add_path(props, "export_location", "Export Location", obs.OBS_PATH_DIRECTORY, "", "")
  obs.obs_properties_add_text(props, "export_suffix", "Export Suffix", obs.OBS_TEXT_DEFAULT)
  obs.obs_properties_add_button(props, "export_button", "Export Package", lambda props, prop: export_files())
  return props

def script_update(settings):
  global save_location, suffix
  save_location = obs.obs_data_get_string(settings, "export_location")
  suffix = obs.obs_data_get_string(settings, "export_suffix")

def get_all_source_paths():
    sources = []
    for source in obs.obs_enum_sources():
        if (obs.obs_source_get_type(source) == obs.OBS_SOURCE_TYPE_INPUT):
          sources.extend(
             re.findall(
                r'([A-Z]:\/(?:(?:[^<>:\"\/\\|?*]*[^<>:\"\/\\|?*.]\/|..\/)*(?:[^<>:\"\/\\|?*]*[^<>:\"\/\\|?*.]\/?|..\/))?)', 
                json.dumps(obs.obs_data_get_json_pretty(
                  obs.obs_source_get_settings(source))
          )))
    return sources

def slugify(value, allow_unicode=False):
  """
  Taken from https://github.com/django/django/blob/master/django/utils/text.py
  Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
  dashes to single dashes. Remove characters that aren't alphanumerics,
  underscores, or hyphens. Convert to lowercase. Also strip leading and
  trailing whitespace, dashes, and underscores.
  """
  value = str(value)
  if allow_unicode:
    value = unicodedata.normalize('NFKC', value)
  else:
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
  value = re.sub(r'[^\w\s-]', '', value.lower())
  return re.sub(r'[-\s]+', '-', value).strip('-_')

def get_export_foldername():
  return slugify(f"{obs.obs_frontend_get_current_scene_collection()}-{suffix}")

def export_files():
  print(f"Exporting {obs.obs_frontend_get_current_scene_collection()} ({save_location + '/' + get_export_foldername()})...")
  sources = get_all_source_paths()
  export_path = f"{save_location}/{get_export_foldername()}"
  
  # Check if save location and export path are set
  if not save_location or not export_path:
    print("Export location is not set.")
    return
  
  # Check if export directory exists, if not create it
  dir_check = obs.os_opendir(export_path)
  if not dir_check:
    obs.os_mkdir(export_path)
  else:
    obs.os_closedir(dir_check)
  
  # Export each source file to the export path
  for source in sources:
    if obs.os_file_exists(source):
      try:
        folder_category = ""
        match obs.os_get_path_extension(source):
          case ".mp3" | ".wav" | ".ogg" | ".flac" | ".aac" | ".m4a":
            folder_category = "Audio"
          case ".mp4" | ".avi" | ".mov" | ".mkv" | "webm" | ".flv" | ".wmv":
            folder_category = "Video"
          case ".png" | ".jpg" | ".jpeg" | ".gif" | ".bmp" | ".tiff" | ".webp" | ".svg":
            folder_category = "Images"
          case " .json" | ".xml" | ".txt" | ".csv":
            folder_category = "Text / Data"
          case _:
            folder_category = "Other"
        obs.os_copyfile(source, f"{export_path}/{folder_category}/{source.split('/')[-1]}")
      except:
        print(f"Failed to copy {source} to {export_path}")
      else:
        print(f"Exported: {source} to {export_path}")
    else:
      print(f"Source file does not exist: {source}")
