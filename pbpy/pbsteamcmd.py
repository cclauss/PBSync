from pathlib import Path
import shutil

from pbpy import pblog, pbtools, pbconfig

def publish_build(branch_type, steamcmd_exec_path, publish_stagedir, app_script, drm_app_id, drm_exe_path):
  # Test if our configuration values exist
  if not app_script:
    pblog.error("steamcmd was not configured.")
    return False

  # The basic needed command line to get into steamcmd
  base_steamcmd_command = [steamcmd_exec_path, "+login", pbconfig.get_user("steamcmd", "username"), pbconfig.get_user("steamcmd", "password")]
  
  # if drm wrapping is configured
  if drm_app_id and drm_exe_path:
    if not Path.is_absolute(drm_exe_path):
      drm_exe_path = (Path(pbconfig.config_filepath).parent / drm_exe_path).resolve()
    if not Path.is_file(drm_exe_path):
      pblog.error("steamcmd/drm/targetbinary does not exist.")
      return False
    drm_command = base_steamcmd_command.copy()
    drm_output = "wrappedBin" + Path(drm_exe_path).suffix # save file to wrappedBin.exe temporarily
    drm_command.extend(["+drm_wrap", drm_exe_path, drm_output, "drmtoolp", "0", "+quit"]) # the drm wrap command https://partner.steamgames.com/doc/features/drm
    pblog.info("Wrapping game with steamworks DRM...")
    drm_proc = pbtools.run_with_output(drm_command)
    pbtools.remove_file(drm_exe_path) # remove original file in any case
    if drm_proc.returncode != 0:
      pblog.error("Drm wrapping failed(%d)" % drm_proc.returncode)
      if Path.exists(drm_output):
        pbtools.remove_file(drm_output)
      return False
    
    shutil.move(drm_output, drm_exe_path) # move drm-wrapped file to location of original
  
  script_path = (Path() / app_script.format(branch_type)).resolve()
  build_cmd = base_steamcmd_command.copy()
  build_cmd.extend(["+run_app_build", script_path, "+quit"])
  proc = pbtools.run(build_cmd)
  result = proc.returncode
  
  if Path.is_file(drm_exe_path):
    pbtools.remove_file(drm_exe_path) # remove drm wrapped file, so that a subsequent build will re-build a non-wrapped executable
  
  return result
