"""
kk - 纯装x
赠与账户，禁用，删除
"""
import asyncio
import pyrogram
from pyrogram import filters
from pyrogram.errors import BadRequest
from bot import bot, prefixes, owner, admins, LOGGER, extra_emby_libs, config
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import cr_kk_ikb, gog_rester_ikb
from bot.func_helper.msg_utils import deleteMessage, sendMessage, editMessage
from bot.func_helper.utils import judge_admins, cr_link_two, tem_deluser
from bot.sql_helper.sql_emby import sql_add_emby, sql_get_emby, sql_update_emby, Emby


# 管理用户
@bot.on_message(filters.command('kk', prefixes) & admins_on_filter)
async def user_info(_, msg):
    await deleteMessage(msg)
    if msg.reply_to_message is None:
        try:
            uid = int(msg.command[1])
            if not msg.sender_chat:
                if msg.from_user.id != owner and uid == owner:
                    return await sendMessage(msg,
                                             f"⭕ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})！不可以偷窥主人",
                                             timer=60)
            else:
                pass
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, ValueError):
            return await sendMessage(msg, '**请先给我一个tg_id！**\n\n用法：/kk [tg_id]\n或者对某人回复kk', timer=60)
        except BadRequest:
            return await sendMessage(msg, f'{msg.command[1]} - 🎂抱歉，此id未登记bot，或者id错误', timer=60)
        except AttributeError:
            pass
        else:
            sql_add_emby(uid)
            text, keyboard = await cr_kk_ikb(uid, first.first_name)
            await sendMessage(msg, text=text, buttons=keyboard)  # protect_content=True 移除禁止复制

    else:
        uid = msg.reply_to_message.from_user.id
        try:
            if msg.from_user.id != owner and uid == owner:
                return await msg.reply(
                    f"⭕ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})！不可以偷窥主人")
        except AttributeError:
            pass

        sql_add_emby(uid)
        text, keyboard = await cr_kk_ikb(uid, msg.reply_to_message.from_user.first_name)
        await sendMessage(msg, text=text, buttons=keyboard)


# 封禁或者解除
@bot.on_callback_query(filters.regex('user_ban'))
async def kk_user_ban(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    b = int(call.data.split("-")[1])
    if b in admins and b != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决",
                                 timer=60)

    first = await bot.get_chat(b)
    e = sql_get_emby(tg=b)
    if e.embyid is None:
        await editMessage(call, f'💢 ta 没有注册账户。', timer=60)
    else:
        text = f'🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 对 [{first.first_name}](tg://user?id={b}) - {e.name} 的'
        if e.lv != "c":
            if await emby.emby_change_policy(id=e.embyid, method=True) is True:
                if sql_update_emby(Emby.tg == b, lv='c') is True:
                    text += f'封禁完成，此状态可在下次续期时刷新'
                    LOGGER.info(text)
                else:
                    text += '封禁失败，已执行，但数据库写入错误'
                    LOGGER.error(text)
            else:
                text += f'封禁失败，请检查emby服务器。响应错误'
                LOGGER.error(text)
        elif e.lv == "c":
            if await emby.emby_change_policy(id=e.embyid):
                if sql_update_emby(Emby.tg == b, lv='b'):
                    text += '解禁完成'
                    LOGGER.info(text)
                else:
                    text += '解禁失败，服务器已执行，数据库写入错误'
                    LOGGER.error(text)
            else:
                text += '解封失败，请检查emby服务器。响应错误'
                LOGGER.error(text)
        await editMessage(call, text)
        await bot.send_message(b, text)


# 开通额外媒体库
@bot.on_callback_query(filters.regex('embyextralib_unblock'))
async def user_embyextralib_unblock(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)
    await call.answer(f'🎬 正在为TA开启显示ing')
    tgid = int(call.data.split("-")[1])
    e = sql_get_emby(tg=tgid)
    if e.embyid is None:
        await editMessage(call, f'💢 ta 没有注册账户。', timer=60)
    embyid = e.embyid
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
            # 保留不同的元素
            currentblock = [x for x in currentblock if x not in extra_emby_libs] + [x for x in extra_emby_libs if
                                                                                    x not in currentblock]
        except KeyError:
            currentblock = ["播放列表"]
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            await editMessage(call, f'🌟 好的，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n'
                                    f'已开启了 [TA](tg://user?id={tgid}) 的额外媒体库权限\n{extra_emby_libs}')
        else:
            await editMessage(call,
                              f'🌧️ Error！管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n操作失败请检查设置！')


# 隐藏额外媒体库
@bot.on_callback_query(filters.regex('embyextralib_block'))
async def user_embyextralib_block(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)
    await call.answer(f'🎬 正在为TA关闭显示ing')
    tgid = int(call.data.split("-")[1])
    e = sql_get_emby(tg=tgid)
    if e.embyid is None:
        await editMessage(call, f'💢 ta 没有注册账户。', timer=60)
    embyid = e.embyid
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
            currentblock = list(set(currentblock + extra_emby_libs))
        except KeyError:
            currentblock = ["播放列表"] + extra_emby_libs
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            await editMessage(call, f'🌟 好的，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n'
                                    f'已关闭了 [TA](tg://user?id={tgid}) 的额外媒体库权限\n{extra_emby_libs}')
        else:
            await editMessage(call,
                              f'🌧️ Error！管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n操作失败请检查设置！')


# 赠送资格
@bot.on_callback_query(filters.regex('gift'))
async def gift(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    b = int(call.data.split("-")[1])
    if b in admins and b != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")

    first = await bot.get_chat(b)
    e = sql_get_emby(tg=b)
    if e.embyid is None:
        link = await cr_link_two(tg=call.from_user.id, for_tg=b, days=config.kk_gift_days)
        await editMessage(call, f"🌟 好的，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n"
                                f'已为 [{first.first_name}](tg://user?id={b}) 赠予资格。前往bot进行下一步操作：',
                          buttons=gog_rester_ikb(link))
        LOGGER.info(f"【admin】：{call.from_user.id} 已发送 注册资格 {first.first_name} - {b} ")
    else:
        await editMessage(call, f'💢 [ta](tg://user?id={b}) 已注册账户。')


# 删除账户
@bot.on_callback_query(filters.regex('closeemby'))
async def close_emby(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    b = int(call.data.split("-")[1])
    if b in admins and b != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决",
                                 timer=60)

    first = await bot.get_chat(b)
    e = sql_get_emby(tg=b)
    if e.embyid is None:
        return await editMessage(call, f'💢 ta 还没有注册账户。', timer=60)

    if await emby.emby_del(e.embyid):
        sql_update_emby(Emby.embyid == e.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None, ex=None)
        tem_deluser()
        await editMessage(call,
                          f'🎯 done，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n等级：{e.lv} - [{first.first_name}](tg://user?id={b}) '
                          f'账户 {e.name} 已完成删除。')
        await bot.send_message(b,
                               f"🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已删除 您 的账户 {e.name}")
        LOGGER.info(f"【admin】：{call.from_user.id} 完成删除 {b} 的账户 {e.name}")
    else:
        await editMessage(call, f'🎯 done，等级：{e.lv} - {first.first_name}的账户 {e.name} 删除失败。')
        LOGGER.info(f"【admin】：{call.from_user.id} 对 {b} 的账户 {e.name} 删除失败 ")


@bot.on_callback_query(filters.regex('fuckoff'))
async def fuck_off_m(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    user_id = int(call.data.split("-")[1])
    if user_id in admins and user_id != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决",
                                 timer=60)
    try:
        user = await bot.get_chat(user_id)
        await call.message.chat.ban_member(user_id)  # 默认退群了就删号    fix：call 没有对象chat
        await editMessage(call,
                          f'🎯 done，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已移除 [{user.first_name}](tg://user?id={user_id})[{user_id}]')
        LOGGER.info(
            f"【admin】：{call.from_user.id} 已从群组 {call.message.chat.id} 封禁 {user.first_name} - {user.id}")
    except pyrogram.errors.ChatAdminRequired:
        await editMessage(call,
                          f"⚠️ 请赋予我踢出成员的权限 [{call.from_user.first_name}](tg://user?id={call.from_user.id})")
    except pyrogram.errors.UserAdminInvalid:
        await editMessage(call,
                          f"⚠️ 打咩，no，机器人不可以对群组管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")


# 设备管理
@bot.on_callback_query(filters.regex('user_devices_manage'))
async def user_devices_manage(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("🔍 正在获取设备信息...")
    uid = int(call.data.split("-")[1])
    
    try:
        first = await bot.get_chat(uid)
        e = sql_get_emby(tg=uid)
        
        if e is None or e.embyid is None:
            return await editMessage(call, f'💢 [{first.first_name}](tg://user?id={uid}) 还没有注册账户。', timer=60)
        
        # 获取用户的已注册设备
        success_devices, devices = await emby.get_user_devices(e.embyid)
        # 获取当前活跃会话
        success_sessions, sessions = await emby.get_user_sessions(e.embyid)
        
        if not success_devices:
            return await editMessage(call, f'💢 [{first.first_name}](tg://user?id={uid}) 获取设备信息失败。', timer=60)
        
        user_devices = devices if success_devices else []
        active_sessions = sessions if success_sessions else []
        
        if not user_devices:
            return await editMessage(call, f'💢 [{first.first_name}](tg://user?id={uid}) 没有注册设备。', timer=60)
        
        # 构建设备信息
        text = f'**💠 [{first.first_name}](tg://user?id={uid}) 的设备管理**\n\n'
        text += f'**已注册设备数：{len(user_devices)}**\n'
        text += f'**当前活跃会话：{len(active_sessions)}**\n\n'
        text += '**设备列表：**\n'
        
        # 创建设备按钮
        keyboard = []
        device_details = ""
        
        for i, device in enumerate(user_devices, 1):
            device_id = device.get("Id", "")
            device_name = device.get("Name", "未知设备")
            app_name = device.get("AppName", "未知应用")
            app_version = device.get("AppVersion", "")
            last_activity = device.get("LastUserActivityDate", "").split("T")[0] if device.get("LastUserActivityDate") else "未知"
            
            # 检查是否有活跃会话
            is_active = any(
                session.get("DeviceId") == device_id 
                for session in active_sessions
            )
            
            status = "🟢在线" if is_active else "⚫离线"
            device_details += f'{i}. {device_name} | {app_name} {app_version} ({status})\n'
            device_details += f'   最后活动: {last_activity}\n\n'
            
            # 为每个设备创建按钮
            if len(device_name + app_name) > 25:
                button_text = f"{device_name[:15]}...| {app_name}"
            else:
                button_text = f"{device_name} | {app_name}"
                
            keyboard.append([[f"🗑️ {button_text}", f'device_action-{uid}-{device_id}']])
        
        text += device_details
        text += '点击设备按钮选择操作方式\n'
        text += '🔸 **终止会话**：断开当前连接，设备仍保持注册\n'
        text += '🔸 **删除设备**：彻底移除设备注册，需重新认证'
        
        keyboard.append([['🔙 返回', f'kk_back-{uid}'], ['❌ 关闭', 'closeit']])
        
        from bot.func_helper.fix_bottons import ikb
        await editMessage(call, text, buttons=ikb(keyboard))
        
    except Exception as e:
        LOGGER.error(f"设备管理错误: {str(e)}")
        await editMessage(call, f'💢 获取设备信息失败：{str(e)}', timer=60)


# 设备操作选择
@bot.on_callback_query(filters.regex('device_action'))
async def device_action(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("🎯 选择操作方式")
    
    try:
        parts = call.data.split("-")
        uid = int(parts[1])
        device_id = parts[2]
        
        first = await bot.get_chat(uid)
        
        text = f'**🎯 设备操作选择**\n\n'
        text += f'**用户：** [{first.first_name}](tg://user?id={uid})\n'
        text += f'**设备ID：** `{device_id}`\n\n'
        text += '请选择操作方式：\n\n'
        text += '🔸 **终止会话**：断开当前连接，设备仍保持注册\n'
        text += '🔸 **删除设备**：彻底移除设备注册，需重新认证'
        
        keyboard = [
            [['⚡ 终止会话', f'kick_session-{uid}-{device_id}']],
            [['🗑️ 删除设备', f'delete_device-{uid}-{device_id}']],
            [['🔙 返回设备列表', f'user_devices_manage-{uid}'], ['❌ 关闭', 'closeit']]
        ]
        
        from bot.func_helper.fix_bottons import ikb
        await editMessage(call, text, buttons=ikb(keyboard))
        
    except Exception as e:
        LOGGER.error(f"设备操作选择错误: {str(e)}")
        await editMessage(call, f'💢 操作失败：{str(e)}', timer=5)


# 终止会话
@bot.on_callback_query(filters.regex('kick_session'))
async def kick_session(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("⚡ 正在终止会话...")
    
    try:
        parts = call.data.split("-")
        uid = int(parts[1])
        device_id = parts[2]
        
        first = await bot.get_chat(uid)
        e = sql_get_emby(tg=uid)
        
        # 获取该设备的活跃会话
        success, sessions = await emby.get_user_sessions(e.embyid)
        if not success:
            return await editMessage(call, f'❌ 获取会话失败', timer=5)
        
        # 找到对应设备的会话
        target_sessions = [s for s in sessions if s.get("DeviceId") == device_id]
        
        if not target_sessions:
            return await editMessage(call, f'💡 该设备当前没有活跃会话', timer=5)
        
        # 终止所有相关会话
        success_count = 0
        for session in target_sessions:
            session_id = session.get("Id")
            if await emby.terminate_session(session_id, f"管理员 {call.from_user.first_name} 终止会话"):
                success_count += 1
        
        if success_count > 0:
            await editMessage(call, f'✅ 已成功终止 [{first.first_name}](tg://user?id={uid}) 的 {success_count} 个会话\n\n正在返回设备列表...', timer=3)
            LOGGER.info(f"【设备管理】：管理员 {call.from_user.id} 终止了用户 {uid} 的设备会话，设备ID: {device_id}")
        else:
            await editMessage(call, f'❌ 终止会话失败', timer=5)
            return
            
        # 2秒后返回设备管理页面
        await asyncio.sleep(2)
        call.data = f'user_devices_manage-{uid}'
        await user_devices_manage(_, call)
            
    except Exception as e:
        LOGGER.error(f"终止会话错误: {str(e)}")
        await editMessage(call, f'💢 终止会话失败：{str(e)}', timer=5)


# 删除设备
@bot.on_callback_query(filters.regex('delete_device'))
async def delete_device_callback(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("🗑️ 正在删除设备...")
    
    try:
        parts = call.data.split("-")
        uid = int(parts[1])
        device_id = parts[2]
        
        first = await bot.get_chat(uid)
        
        # 删除设备注册
        success = await emby.delete_device(device_id)
        
        if success:
            await editMessage(call, f'✅ 已成功删除 [{first.first_name}](tg://user?id={uid}) 的设备\n\n设备已从服务器彻底移除，需重新认证\n\n正在返回设备列表...', timer=3)
            LOGGER.info(f"【设备管理】：管理员 {call.from_user.id} 删除了用户 {uid} 的设备，设备ID: {device_id}")
            
            # 2秒后返回设备管理页面
            await asyncio.sleep(2)
            call.data = f'user_devices_manage-{uid}'
            await user_devices_manage(_, call)
        else:
            await editMessage(call, f'❌ 删除设备失败，请检查服务器连接', timer=5)
            
    except Exception as e:
        LOGGER.error(f"删除设备错误: {str(e)}")
        await editMessage(call, f'💢 删除设备失败：{str(e)}', timer=5)


# 返回kk面板
@bot.on_callback_query(filters.regex('kk_back'))
async def kk_back(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    uid = int(call.data.split("-")[1])
    
    try:
        first = await bot.get_chat(uid)
        text, keyboard = await cr_kk_ikb(uid, first.first_name)
        await editMessage(call, text, buttons=keyboard)
    except Exception as e:
        LOGGER.error(f"返回kk面板错误: {str(e)}")
        await editMessage(call, f'💢 返回失败：{str(e)}', timer=5)
