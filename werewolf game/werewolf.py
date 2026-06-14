#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/6/13 21:22

async def werewolf_phase(self, round_num: int):
	"""狼人阶段 - 展示消息驱动的协作模式"""
	if not self.werewolves:
		return None

	# 通过消息中心建立狼人专属通信频道
	async with MsgHub(
			self.werewolves,
			enable_auto_broadcast=True,
			announcement=await self.moderator.announce(
				f"狼人们，请讨论今晚的击杀目标。存活玩家：{format_player_list(self.alive_players)}"
			),
	) as werewolves_hub:
		# 讨论阶段：狼人通过消息交换策略
		for _ in range(MAX_DISCUSSION_ROUND):
			for wolf in self.werewolves:
				await wolf(structured_model=DiscussionModelCN)

		# 投票阶段：收集并统计狼人的击杀决策
		werewolves_hub.set_auto_broadcast(False)
		kill_votes = await fanout_pipeline(
			self.werewolves,
			msg=await self.moderator.announce("请选择击杀目标"),
			structured_model=WerewolfKillModelCN,
			enable_gather=False,
		)
