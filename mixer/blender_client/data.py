"""
This module handles generic updates using the blender_data package.

The goal for Mixer is to replace all code specific to entities (camera, light, material, ...) by this generic update
mechanism.
"""

import logging
import traceback

from mixer.blender_data.json_codec import Codec
from mixer.blender_data.proxy import CreationChangeset, RemovalChangeset, UpdateChangeset, RenameChangeset, Delta
from mixer.broadcaster import common
from mixer.share_data import share_data

logger = logging.getLogger(__name__)


def send_data_creations(proxies: CreationChangeset):
    if not share_data.use_experimental_sync():
        return

    codec = Codec()
    for proxy in proxies:
        logger.info("%s %s", "send_data_create", proxy)

        try:
            encoded_proxy = codec.encode(proxy)
        except Exception:
            logger.error(f"send_data_create: encode exception for {proxy}")
            for line in traceback.format_exc().splitlines():
                logger.error(line)
            continue

        buffer = common.encode_string(encoded_proxy)
        command = common.Command(common.MessageType.BLENDER_DATA_CREATE, buffer, 0)
        share_data.client.add_command(command)


def send_data_updates(updates: UpdateChangeset):
    if not share_data.use_experimental_sync():
        return

    codec = Codec()
    for update in updates:
        logger.info("%s %s", "send_data_update", update)

        try:
            encoded_update = codec.encode(update)
        except Exception:
            logger.error(f"send_data_update: encode exception for {update}")
            for line in traceback.format_exc().splitlines():
                logger.error(line)
            continue

        buffer = common.encode_string(encoded_update)
        command = common.Command(common.MessageType.BLENDER_DATA_UPDATE, buffer, 0)
        share_data.client.add_command(command)


def build_data_create(buffer):
    if not share_data.use_experimental_sync():
        return

    buffer, _ = common.decode_string(buffer, 0)
    codec = Codec()
    rename_changeset = None

    try:
        id_proxy = codec.decode(buffer)
        logger.info("%s: %s", "build_data_create", id_proxy)
        # TODO temporary until VRtist protocol uses Blenddata instead of blender_objects & co
        share_data.set_dirty()
        _, rename_changeset = share_data.bpy_data_proxy.create_datablock(id_proxy)
    except Exception:
        logger.error(f"Exception during build_data_create")
        for line in traceback.format_exc().splitlines():
            logger.error(line)
        logger.error(f"During processing of buffer for {id_proxy}")
        logger.error(buffer[0:200])
        logger.error("...")
        logger.error(buffer[-200:0])
        logger.error(f"ignored")

    if rename_changeset:
        send_data_renames(rename_changeset)


def build_data_update(buffer):
    if not share_data.use_experimental_sync():
        return

    buffer, _ = common.decode_string(buffer, 0)
    codec = Codec()

    try:
        delta: Delta = codec.decode(buffer)
        logger.info("%s: %s", "build_data_update", delta)
        # TODO temporary until VRtist protocol uses Blenddata instead of blender_objects & co
        share_data.set_dirty()
        share_data.bpy_data_proxy.update_datablock(delta)
    except Exception:
        logger.error(f"Exception during build_data_update")
        for line in traceback.format_exc().splitlines():
            logger.error(line)
        logger.error(f"During processing of buffer for {delta}")
        logger.error(buffer[0:200])
        logger.error("...")
        logger.error(buffer[-200:0])
        logger.error(f"ignored")


def send_data_removals(removals: RemovalChangeset):
    if not share_data.use_experimental_sync():
        return

    for uuid, debug_info in removals:
        logger.info("send_removal: %s (%s)", uuid, debug_info)
        buffer = common.encode_string(uuid) + common.encode_string(debug_info)
        command = common.Command(common.MessageType.BLENDER_DATA_REMOVE, buffer, 0)
        share_data.client.add_command(command)


def build_data_remove(buffer):
    if not share_data.use_experimental_sync():
        return

    uuid, index = common.decode_string(buffer, 0)
    debug_info, index = common.decode_string(buffer, index)
    logger.info("build_data_remove: %s (%s)", uuid, debug_info)
    share_data.bpy_data_proxy.remove_datablock(uuid)

    # TODO temporary until VRtist protocol uses Blenddata instead of blender_objects & co
    share_data.set_dirty()


def send_data_renames(renames: RenameChangeset):
    if not share_data.use_experimental_sync():
        return

    for uuid, new_name, debug_info in renames:
        logger.info("send_rename: %s (%s) into %s", uuid, debug_info, new_name)
        buffer = common.encode_string(uuid) + common.encode_string(new_name) + common.encode_string(debug_info)
        command = common.Command(common.MessageType.BLENDER_DATA_RENAME, buffer, 0)
        share_data.client.add_command(command)


def build_data_rename(buffer):
    if not share_data.use_experimental_sync():
        return

    uuid, index = common.decode_string(buffer, 0)
    new_name, index = common.decode_string(buffer, index)
    debug_info, index = common.decode_string(buffer, index)
    logger.info("build_data_rename: %s (%s) into %s", uuid, debug_info, new_name)
    share_data.bpy_data_proxy.rename_datablock(uuid, new_name)

    # TODO temporary until VRtist protocol uses Blenddata instead of blender_objects & co
    share_data.set_dirty()
