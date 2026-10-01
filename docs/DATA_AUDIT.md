# Data Audit

**Generated** by `scripts/audit_raw_fields.py` from the raw corpus on disk. Do not edit by hand; re-run the script instead.

This file is the **sole home for data-availability facts** in this repository. Domain documents describe how the game works and must not restate anything measured here. Everything below is measured over the whole corpus, never sampled.

---

## 1. Corpus inventory

| Check | Count |
|---|---|
| Match detail files | 825 |
| Timeline files | 825 |
| **Valid pairs** | **825** |
| Detail missing a timeline | 0 |
| Timeline missing a detail | 0 |
| Duplicate match IDs | 0 |
| Malformed / unparseable | 0 |
| Structurally incomplete | 0 |
| **Audited** | **825** |

Every later phase operates on the audited set. Orphans, duplicates, malformed files and structurally incomplete pairs are excluded and listed, never skipped silently.

---

## 2. Measurements the schema design depends on

### 2.1 Frame interval

Decides what is observable at all. A uniform 60000 ms means per-minute resolution and nothing finer, which is what rules out direct wave-state reconstruction and frame-by-frame trade analysis.

| frameInterval (ms) | Count | Share |
|---|---|---|
| `60000` | 825 | 100.0% |

Frames per match: min 3, median 31, mean 30.4, max 58

### 2.2 Kill damage attribution

`victimDamageDealt` and `victimDamageReceived` on `CHAMPION_KILL` carry per-source damage in the seconds before a death -- the only sub-minute resolution available anywhere in this data. Death context and external-pressure analysis depend on them.

| Measure | Value |
|---|---|
| CHAMPION_KILL events | 57,690 |
| Kills per match | min 0, median 71, mean 69.9, max 161 |
| `victimDamageDealt` present | 92.8% (53,510 of 57,690) |
| `victimDamageDealt` missing | 4,180 |
| `victimDamageDealt` entries per kill | min 1, median 6, mean 6.8, max 44 |
| `victimDamageReceived` present | 100.0% (57,690 of 57,690) |
| `victimDamageReceived` missing | 0 |
| `victimDamageReceived` entries per kill | min 1, median 11, mean 11.8, max 45 |

**`victimDamageDealt` absence is semantic, not a patch gap.** The missing rate is spread evenly across every patch in the corpus (table below), with no cliff at any version boundary, and 98.0% of the affected kills were made by a champion rather than an execution. The field is absent when the victim dealt no damage before dying. **Read absence as an empty list, not as unavailable data** -- no fallback is required and `victimDamageReceived` is present on every kill.

| Patch | Kills | `victimDamageDealt` missing | Rate |
|---|---|---|---|
| `15.18` | 709 | 31 | 4.4% |
| `15.19` | 1,418 | 91 | 6.4% |
| `15.20` | 505 | 38 | 7.5% |
| `15.21` | 232 | 5 | 2.2% |
| `15.22` | 235 | 11 | 4.7% |
| `15.23` | 1,427 | 72 | 5.0% |
| `15.24` | 4,354 | 226 | 5.2% |
| `16.1` | 5,294 | 264 | 5.0% |
| `16.2` | 2,035 | 101 | 5.0% |
| `16.3` | 3,519 | 286 | 8.1% |
| `16.4` | 347 | 24 | 6.9% |
| `16.5` | 419 | 33 | 7.9% |
| `16.6` | 1,792 | 125 | 7.0% |
| `16.7` | 1,575 | 115 | 7.3% |
| `16.8` | 1,480 | 117 | 7.9% |
| `16.9` | 2,876 | 238 | 8.3% |
| `16.10` | 4,697 | 369 | 7.9% |
| `16.11` | 2,509 | 223 | 8.9% |
| `16.12` | 997 | 77 | 7.7% |
| `16.13` | 4,655 | 397 | 8.5% |
| `16.14` | 2,542 | 198 | 7.8% |
| `16.15` | 2,697 | 228 | 8.5% |
| `16.16` | 6,188 | 506 | 8.2% |
| `16.17` | 5,188 | 405 | 7.8% |

### 2.3 Participants, positions and patches

Participant rows: 8,250

| Participants per match | Count | Share |
|---|---|---|
| `10` | 825 | 100.0% |

| teamPosition | Count | Share |
|---|---|---|
| `BOTTOM` | 1,650 | 20.0% |
| `MIDDLE` | 1,650 | 20.0% |
| `TOP` | 1,650 | 20.0% |
| `JUNGLE` | 1,649 | 20.0% |
| `UTILITY` | 1,649 | 20.0% |
| `<blank>` | 2 | 0.0% |

`challenges` keys per participant: min 118, median 128, mean 128.2, max 135

| queueId | Count | Share |
|---|---|---|
| `420` | 825 | 100.0% |

| Patch | Count | Share |
|---|---|---|
| `16.16` | 88 | 10.7% |
| `16.17` | 79 | 9.6% |
| `16.1` | 69 | 8.4% |
| `16.10` | 67 | 8.1% |
| `16.13` | 67 | 8.1% |
| `15.24` | 64 | 7.8% |
| `16.3` | 54 | 6.5% |
| `16.9` | 39 | 4.7% |
| `16.15` | 38 | 4.6% |
| `16.14` | 37 | 4.5% |
| `16.11` | 34 | 4.1% |
| `16.2` | 30 | 3.6% |
| `16.6` | 26 | 3.2% |
| `16.7` | 22 | 2.7% |
| `15.23` | 21 | 2.5% |
| `16.8` | 21 | 2.5% |
| `15.19` | 20 | 2.4% |
| `16.12` | 16 | 1.9% |
| `15.18` | 9 | 1.1% |
| `15.20` | 7 | 0.8% |
| `16.5` | 6 | 0.7% |
| `16.4` | 5 | 0.6% |
| `15.21` | 3 | 0.4% |
| `15.22` | 3 | 0.4% |

### 2.4 Degenerate games

Matches with fewer than 10 timeline frames, and matches where any participant has a blank `teamPosition`. Both are listed as diagnostics. **Whether these are excluded from analysis is a scope decision, not a parsing decision** -- they are real games, they parse cleanly, and the canonical layer should hold them. No remake threshold is invented here.

Short matches: **16** of 825 (1.9%).

| Match | Frames | Duration (s) | Patch | Result |
|---|---|---|---|---|
| `VN2_1260896690` | 3 | 104 | `16.3` | GameComplete |
| `VN2_1263268632` | 3 | 77 | `16.3` | GameComplete |
| `VN2_1333869686` | 3 | 72 | `16.7` | GameComplete |
| `VN2_1347555220` | 3 | 92 | `16.8` | GameComplete |
| `VN2_1395318391` | 3 | 85 | `16.10` | GameComplete |
| `VN2_1395411511` | 3 | 81 | `16.10` | GameComplete |
| `VN2_1485002902` | 3 | 68 | `16.13` | GameComplete |
| `VN2_1496058015` | 3 | 79 | `16.13` | GameComplete |
| `VN2_1574644462` | 3 | 75 | `16.17` | GameComplete |
| `VN2_1144550518` | 4 | 176 | `15.23` | GameComplete |
| `VN2_1188613875` | 4 | 125 | `15.24` | GameComplete |
| `VN2_1382264559` | 4 | 123 | `16.9` | GameComplete |
| `VN2_1574339498` | 4 | 128 | `16.17` | GameComplete |
| `VN2_1503217698` | 8 | 387 | `16.14` | GameComplete |
| `VN2_1317614741` | 9 | 438 | `16.6` | GameComplete |
| `VN2_1554839806` | 9 | 426 | `16.16` | GameComplete |

Blank `teamPosition` matches: **1**.

| Match | Frames | Patch |
|---|---|---|
| `VN2_1382264559` | 4 | `16.9` |

---

## 3. Field inventory

Every JSON leaf path observed, with the share of audited matches containing it. List indices are collapsed to `[]`. `PARTIAL` marks a path present in fewer than 99% of matches -- building on one needs a documented fallback. `IDENTIFIER` marks an account identifier that is measured here but must never be ingested.

### 3.1 Match detail

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `info.endOfGameResult` | 100.0% | 825 | 0.0% | str |  |
| `info.gameCreation` | 100.0% | 825 | 0.0% | int |  |
| `info.gameDuration` | 100.0% | 825 | 0.0% | int |  |
| `info.gameEndTimestamp` | 100.0% | 825 | 0.0% | int |  |
| `info.gameId` | 100.0% | 825 | 0.0% | int |  |
| `info.gameMode` | 100.0% | 825 | 0.0% | str |  |
| `info.gameName` | 100.0% | 825 | 0.0% | str |  |
| `info.gameStartTimestamp` | 100.0% | 825 | 0.0% | int |  |
| `info.gameType` | 100.0% | 825 | 0.0% | str |  |
| `info.gameVersion` | 100.0% | 825 | 0.0% | str |  |
| `info.mapId` | 100.0% | 825 | 0.0% | int |  |
| `info.participants[].PlayerBehavior.PlayerBehavior_IsHeroInCombat` | 66.1% | 5,450 | 0.0% | int | PARTIAL |
| `info.participants[].PlayerScore0` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore1` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore10` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore11` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore2` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore3` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore4` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore5` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore6` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore7` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore8` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].PlayerScore9` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].allInPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].assistMePings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].assists` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].baronKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].basicPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].causedGameEndFromIGNBSurrender` | 51.6% | 4,260 | 0.0% | bool | PARTIAL |
| `info.participants[].challenges.12AssistStreakCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.HealFromMapSources` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.InfernalScalePickup` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_DefeatAatrox` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_DefeatBriar` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_DefeatMiniBosses` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_EvolveWeapon` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_Have3Passives` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_KillEnemy` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_PickupGold` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_ReachLevel50` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_Survive15Min` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.SWARM_WinWith5EvolvedWeapons` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.abilityUses` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.acesBefore15Minutes` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.alliedJungleMonsterKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.baronBuffGoldAdvantageOverThreshold` | 46.8% | 1,980 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.baronTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.blastConeOppositeOpponentCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.bountyGold` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.buffsStolen` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.completeSupportQuestInTime` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.controlWardTimeCoverageInRiverOrEnemyHalf` | 98.2% | 4,898 | 0.0% | float | PARTIAL |
| `info.participants[].challenges.controlWardsPlaced` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.damagePerMinute` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.damageTakenOnTeamPercentage` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.dancedWithRiftHerald` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.deathsByEnemyChamps` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.dodgeSkillShotsSmallWindow` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.doubleAces` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.dragonTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.earliestBaron` | 77.3% | 3,700 | 0.0% | float | PARTIAL |
| `info.participants[].challenges.earliestDragonTakedown` | 98.2% | 4,487 | 0.0% | float | PARTIAL |
| `info.participants[].challenges.earliestElderDragon` | 6.7% | 295 | 0.0% | float | PARTIAL |
| `info.participants[].challenges.earlyLaningPhaseGoldExpAdvantage` | 97.9% | 8,080 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.effectiveHealAndShielding` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.elderDragonKillsWithOpposingSoul` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.elderDragonMultikills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.enemyChampionImmobilizations` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.enemyJungleMonsterKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.epicMonsterKillsNearEnemyJungler` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.epicMonsterKillsWithin30SecondsOfSpawn` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.epicMonsterSteals` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.epicMonsterStolenWithoutSmite` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.fasterSupportQuestCompletion` | 47.8% | 395 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.fastestLegendary` | 53.6% | 548 | 0.0% | float | PARTIAL |
| `info.participants[].challenges.firstTurretKilled` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.firstTurretKilledTime` | 97.8% | 4,035 | 0.0% | float | PARTIAL |
| `info.participants[].challenges.fistBumpParticipation` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.flawlessAces` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.fullTeamTakedown` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.gameLength` | 100.0% | 8,250 | 0.0% | float |  |
| `info.participants[].challenges.getTakedownsInAllLanesEarlyJungleAsLaner` | 100.0% | 6,600 | 0.0% | int |  |
| `info.participants[].challenges.goldPerMinute` | 100.0% | 8,250 | 0.0% | float |  |
| `info.participants[].challenges.hadAfkTeammate` | 4.8% | 159 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.hadOpenNexus` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.highestChampionDamage` | 100.0% | 825 | 0.0% | int |  |
| `info.participants[].challenges.highestCrowdControlScore` | 100.0% | 825 | 0.0% | int |  |
| `info.participants[].challenges.highestWardKills` | 98.7% | 962 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.immobilizeAndKillWithAlly` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.initialBuffCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.initialCrabCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.jungleCsBefore10Minutes` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.junglerKillsEarlyJungle` | 100.0% | 1,650 | 0.0% | int |  |
| `info.participants[].challenges.junglerTakedownsNearDamagedEpicMonster` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.kTurretsDestroyedBeforePlatesFall` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.kda` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.killAfterHiddenWithAlly` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.killParticipation` | 99.4% | 8,175 | 0.0% | float, int |  |
| `info.participants[].challenges.killedChampTookFullTeamDamageSurvived` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.killingSprees` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.killsNearEnemyTurret` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.killsOnLanersEarlyJungleAsJungler` | 100.0% | 1,650 | 0.0% | int |  |
| `info.participants[].challenges.killsOnOtherLanesEarlyJungleAsLaner` | 100.0% | 6,600 | 0.0% | int |  |
| `info.participants[].challenges.killsOnRecentlyHealedByAramPack` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.killsUnderOwnTurret` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.killsWithHelpFromEpicMonster` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.knockEnemyIntoTeamAndKill` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.landSkillShotsEarlyGame` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.laneMinionsFirst10Minutes` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.laningPhaseGoldExpAdvantage` | 97.3% | 8,030 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.legendaryCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.legendaryItemUsed[]` | 98.1% | 30,204 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.lostAnInhibitor` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.maxCsAdvantageOnLaneOpponent` | 98.1% | 8,090 | 0.0% | float, int | PARTIAL |
| `info.participants[].challenges.maxKillDeficit` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.maxLevelLeadLaneOpponent` | 98.1% | 8,090 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.mejaisFullStackInTime` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.moreEnemyJungleThanOpponent` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.multiKillOneSpell` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.multiTurretRiftHeraldCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.multikills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.multikillsAfterAggressiveFlash` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.outerTurretExecutesBefore10Minutes` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.outnumberedKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.outnumberedNexusKill` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.perfectDragonSoulsTaken` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.perfectGame` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.pickKillWithAlly` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.playedChampSelectPosition` | 98.1% | 8,090 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.poroExplosions` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.quickCleanse` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.quickFirstTurret` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.quickSoloKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.riftHeraldTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.saveAllyFromDeath` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.scuttleCrabKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.shortestTimeToAceFromFirstTakedown` | 69.8% | 2,246 | 0.0% | float | PARTIAL |
| `info.participants[].challenges.skillshotsDodged` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.skillshotsHit` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.snowballsHit` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.soloBaronKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.soloKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.soloTurretsLategame` | 90.1% | 1,666 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.stealthWardsPlaced` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.survivedSingleDigitHpCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.survivedThreeImmobilizesInFight` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.takedownOnFirstTurret` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.takedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.takedownsAfterGainingLevelAdvantage` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.takedownsBeforeJungleMinionSpawn` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.takedownsFirstXMinutes` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.takedownsInAlcove` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.takedownsInEnemyFountain` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.teamBaronKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.teamDamagePercentage` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.teamElderDragonKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.teamRiftHeraldKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.teleportTakedowns` | 55.6% | 625 | 0.0% | int | PARTIAL |
| `info.participants[].challenges.tookLargeDamageSurvived` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.turretPlatesTaken` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.turretTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.turretsTakenWithRiftHerald` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.twentyMinionsIn3SecondsCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.twoWardsOneSweeperCount` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.unseenRecalls` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.visionScoreAdvantageLaneOpponent` | 98.1% | 8,090 | 0.0% | float, int | PARTIAL |
| `info.participants[].challenges.visionScorePerMinute` | 100.0% | 8,250 | 0.0% | float, int |  |
| `info.participants[].challenges.voidMonsterKill` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.wardTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.wardTakedownsBefore20M` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].challenges.wardsGuarded` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].champExperience` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].champLevel` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].championId` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].championName` | 100.0% | 8,250 | 0.0% | str |  |
| `info.participants[].championTransform` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].commandPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].consumablesPurchased` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].damageDealtToBuildings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].damageDealtToEpicMonsters` | 95.6% | 7,890 | 0.0% | int | PARTIAL |
| `info.participants[].damageDealtToObjectives` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].damageDealtToTurrets` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].damageSelfMitigated` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].dangerPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].deaths` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].detectorWardsPlaced` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].doubleKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].dragonKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].eligibleForProgression` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].enemyMissingPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].enemyVisionPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].firstBloodAssist` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].firstBloodKill` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].firstTowerAssist` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].firstTowerKill` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].gameEndedInEarlySurrender` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].gameEndedInIGNBSurrender` | 56.4% | 4,650 | 0.0% | bool | PARTIAL |
| `info.participants[].gameEndedInSurrender` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].getBackPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].goldEarned` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].goldSpent` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].holdPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].individualPosition` | 100.0% | 8,250 | 0.0% | str |  |
| `info.participants[].inhibitorKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].inhibitorTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].inhibitorsLost` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].item0` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].item1` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].item2` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].item3` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].item4` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].item5` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].item6` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].itemsPurchased` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].killingSprees` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].kills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].lane` | 100.0% | 8,250 | 0.0% | str |  |
| `info.participants[].largestCriticalStrike` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].largestKillingSpree` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].largestMultiKill` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].longestTimeSpentLiving` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].magicDamageDealt` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].magicDamageDealtToChampions` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].magicDamageTaken` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore0` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore1` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore10` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore11` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore2` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore3` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore4` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore5` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore6` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore7` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore8` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].missions.playerScore9` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].needVisionPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].neutralMinionsKilled` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].nexusKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].nexusLost` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].nexusTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].objectivesStolen` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].objectivesStolenAssists` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].onMyWayPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].participantId` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].pentaKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].perks.statPerks.defense` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].perks.statPerks.flex` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].perks.statPerks.offense` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].perks.styles[].description` | 100.0% | 16,500 | 0.0% | str |  |
| `info.participants[].perks.styles[].selections[].perk` | 100.0% | 49,500 | 0.0% | int |  |
| `info.participants[].perks.styles[].selections[].var1` | 100.0% | 49,500 | 0.0% | int |  |
| `info.participants[].perks.styles[].selections[].var2` | 100.0% | 49,500 | 0.0% | int |  |
| `info.participants[].perks.styles[].selections[].var3` | 100.0% | 49,500 | 0.0% | int |  |
| `info.participants[].perks.styles[].style` | 100.0% | 16,500 | 0.0% | int |  |
| `info.participants[].physicalDamageDealt` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].physicalDamageDealtToChampions` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].physicalDamageTaken` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].placement` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].playerAugment1` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].playerAugment2` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].playerAugment3` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].playerAugment4` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].playerAugment5` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].playerAugment6` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].playerSubteamId` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].positionAssignedByMatchmaking` | 43.5% | 3,590 | 0.0% | str | PARTIAL |
| `info.participants[].profileIcon` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].pushPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].puuid` | 100.0% | 8,250 | 0.0% | str | IDENTIFIER - do not ingest |
| `info.participants[].quadraKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].retreatPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].riotIdGameName` | 100.0% | 8,250 | 0.0% | str | IDENTIFIER - do not ingest |
| `info.participants[].riotIdTagline` | 100.0% | 8,250 | 0.0% | str |  |
| `info.participants[].role` | 100.0% | 8,250 | 0.0% | str |  |
| `info.participants[].roleBoundItem` | 84.6% | 6,980 | 0.0% | int | PARTIAL |
| `info.participants[].selectedRolePreferences` | 43.5% | 3,590 | 0.0% | str | PARTIAL |
| `info.participants[].sightWardsBoughtInGame` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].spell1Casts` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].spell2Casts` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].spell3Casts` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].spell4Casts` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].subteamPlacement` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].summoner1Casts` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].summoner1Id` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].summoner2Casts` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].summoner2Id` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].summonerId` | 100.0% | 8,250 | 0.0% | str | IDENTIFIER - do not ingest |
| `info.participants[].summonerLevel` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].summonerName` | 100.0% | 8,250 | 0.0% | str | IDENTIFIER - do not ingest |
| `info.participants[].teamEarlySurrendered` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.participants[].teamIGNBSurrendered` | 56.4% | 4,650 | 0.0% | bool | PARTIAL |
| `info.participants[].teamId` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].teamPosition` | 100.0% | 8,250 | 0.0% | str |  |
| `info.participants[].timeCCingOthers` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].timePlayed` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalAllyJungleMinionsKilled` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalDamageDealt` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalDamageDealtToChampions` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalDamageShieldedOnTeammates` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalDamageTaken` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalEnemyJungleMinionsKilled` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalHeal` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalHealsOnTeammates` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalMinionsKilled` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalTimeCCDealt` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalTimeSpentDead` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].totalUnitsHealed` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].tripleKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].trueDamageDealt` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].trueDamageDealtToChampions` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].trueDamageTaken` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].turretKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].turretTakedowns` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].turretsLost` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].unrealKills` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].visionClearedPings` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].visionScore` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].visionWardsBoughtInGame` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].wardsKilled` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].wardsPlaced` | 100.0% | 8,250 | 0.0% | int |  |
| `info.participants[].wasAfk` | 20.2% | 1,670 | 0.0% | bool | PARTIAL |
| `info.participants[].wasPremadeWithIGNBGameEndCauser` | 51.6% | 4,260 | 0.0% | bool | PARTIAL |
| `info.participants[].wasPremadeWithSevereTransgressor` | 51.6% | 4,260 | 0.0% | bool | PARTIAL |
| `info.participants[].wasSevereTransgressor` | 51.6% | 4,260 | 0.0% | bool | PARTIAL |
| `info.participants[].win` | 100.0% | 8,250 | 0.0% | bool |  |
| `info.platformId` | 100.0% | 825 | 0.0% | str |  |
| `info.queueId` | 100.0% | 825 | 0.0% | int |  |
| `info.teams[].bans[].championId` | 100.0% | 8,250 | 0.0% | int |  |
| `info.teams[].bans[].pickTurn` | 100.0% | 8,250 | 0.0% | int |  |
| `info.teams[].feats.EPIC_MONSTER_KILL.featState` | 38.4% | 634 | 0.0% | int | PARTIAL |
| `info.teams[].feats.FIRST_BLOOD.featState` | 38.4% | 634 | 0.0% | int | PARTIAL |
| `info.teams[].feats.FIRST_TURRET.featState` | 38.4% | 634 | 0.0% | int | PARTIAL |
| `info.teams[].objectives.atakhan.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.atakhan.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].objectives.baron.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.baron.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].objectives.champion.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.champion.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].objectives.dragon.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.dragon.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].objectives.horde.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.horde.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].objectives.inhibitor.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.inhibitor.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].objectives.riftHerald.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.riftHerald.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].objectives.tower.first` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.teams[].objectives.tower.kills` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].teamId` | 100.0% | 1,650 | 0.0% | int |  |
| `info.teams[].win` | 100.0% | 1,650 | 0.0% | bool |  |
| `info.tournamentCode` | 100.0% | 825 | 0.0% | str |  |
| `metadata.dataVersion` | 100.0% | 825 | 0.0% | str |  |
| `metadata.matchId` | 100.0% | 825 | 0.0% | str |  |
| `metadata.participants[]` | 100.0% | 8,250 | 0.0% | str |  |

### 3.2 Timeline participant frames

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `championStats.abilityHaste` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.abilityPower` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.armor` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.armorPen` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.armorPenPercent` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.attackDamage` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.attackSpeed` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.bonusArmorPenPercent` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.bonusMagicPenPercent` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.ccReduction` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.cooldownReduction` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.health` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.healthMax` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.healthRegen` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.lifesteal` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.magicPen` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.magicPenPercent` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.magicResist` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.movementSpeed` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.omnivamp` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.physicalVamp` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.power` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.powerMax` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.powerRegen` | 100.0% | 250,780 | 0.0% | int |  |
| `championStats.spellVamp` | 100.0% | 250,780 | 0.0% | int |  |
| `currentGold` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.magicDamageDone` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.magicDamageDoneToChampions` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.magicDamageTaken` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.physicalDamageDone` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.physicalDamageDoneToChampions` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.physicalDamageTaken` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.totalDamageDone` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.totalDamageDoneToChampions` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.totalDamageTaken` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.trueDamageDone` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.trueDamageDoneToChampions` | 100.0% | 250,780 | 0.0% | int |  |
| `damageStats.trueDamageTaken` | 100.0% | 250,780 | 0.0% | int |  |
| `goldPerSecond` | 100.0% | 250,780 | 0.0% | int |  |
| `jungleMinionsKilled` | 100.0% | 250,780 | 0.0% | int |  |
| `level` | 100.0% | 250,780 | 0.0% | int |  |
| `minionsKilled` | 100.0% | 250,780 | 0.0% | int |  |
| `participantId` | 100.0% | 250,780 | 0.0% | int |  |
| `position.x` | 100.0% | 250,780 | 0.0% | int |  |
| `position.y` | 100.0% | 250,780 | 0.0% | int |  |
| `timeEnemySpentControlled` | 100.0% | 250,780 | 0.0% | int |  |
| `totalGold` | 100.0% | 250,780 | 0.0% | int |  |
| `xp` | 100.0% | 250,780 | 0.0% | int |  |

### 3.3 Timeline events, by type

Presence is measured against matches containing that event type at all, not against the whole corpus.

#### `BUILDING_KILL`

Present in 807 of 825 matches (97.8%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `assistingParticipantIds[]` | 97.6% | 9,923 | 0.0% | int | PARTIAL |
| `bounty` | 100.0% | 11,026 | 0.0% | int |  |
| `buildingType` | 100.0% | 11,026 | 0.0% | str |  |
| `killerId` | 100.0% | 11,026 | 0.0% | int |  |
| `laneType` | 100.0% | 11,026 | 0.0% | str |  |
| `position.x` | 100.0% | 11,026 | 0.0% | int |  |
| `position.y` | 100.0% | 11,026 | 0.0% | int |  |
| `teamId` | 100.0% | 11,026 | 0.0% | int |  |
| `timestamp` | 100.0% | 11,026 | 0.0% | int |  |
| `towerType` | 100.0% | 9,547 | 0.0% | str |  |
| `type` | 100.0% | 11,026 | 0.0% | str |  |

#### `CHAMPION_KILL`

Present in 820 of 825 matches (99.4%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `assistingParticipantIds[]` | 99.9% | 76,690 | 0.0% | int |  |
| `bounty` | 100.0% | 57,690 | 0.0% | int |  |
| `killStreakLength` | 100.0% | 57,690 | 0.0% | int |  |
| `killerId` | 100.0% | 57,690 | 0.0% | int |  |
| `position.x` | 100.0% | 57,690 | 0.0% | int |  |
| `position.y` | 100.0% | 57,690 | 0.0% | int |  |
| `shutdownBounty` | 100.0% | 57,690 | 0.0% | int |  |
| `timestamp` | 100.0% | 57,690 | 0.0% | int |  |
| `type` | 100.0% | 57,690 | 0.0% | str |  |
| `victimDamageDealt[].basic` | 100.0% | 365,844 | 0.0% | bool |  |
| `victimDamageDealt[].magicDamage` | 100.0% | 365,844 | 0.0% | int |  |
| `victimDamageDealt[].name` | 100.0% | 365,844 | 0.0% | str |  |
| `victimDamageDealt[].participantId` | 100.0% | 365,844 | 0.0% | int |  |
| `victimDamageDealt[].physicalDamage` | 100.0% | 365,844 | 0.0% | int |  |
| `victimDamageDealt[].spellName` | 100.0% | 365,844 | 0.0% | str |  |
| `victimDamageDealt[].spellSlot` | 100.0% | 365,844 | 0.0% | int |  |
| `victimDamageDealt[].trueDamage` | 100.0% | 365,844 | 0.0% | int |  |
| `victimDamageDealt[].type` | 100.0% | 365,844 | 0.0% | str |  |
| `victimDamageReceived[].basic` | 100.0% | 682,384 | 0.0% | bool |  |
| `victimDamageReceived[].magicDamage` | 100.0% | 682,384 | 0.0% | int |  |
| `victimDamageReceived[].name` | 100.0% | 682,384 | 0.0% | str |  |
| `victimDamageReceived[].participantId` | 100.0% | 682,384 | 0.0% | int |  |
| `victimDamageReceived[].physicalDamage` | 100.0% | 682,384 | 0.0% | int |  |
| `victimDamageReceived[].spellName` | 100.0% | 682,384 | 0.0% | str |  |
| `victimDamageReceived[].spellSlot` | 100.0% | 682,384 | 0.0% | int |  |
| `victimDamageReceived[].trueDamage` | 100.0% | 682,384 | 0.0% | int |  |
| `victimDamageReceived[].type` | 100.0% | 682,384 | 0.0% | str |  |
| `victimId` | 100.0% | 57,690 | 0.0% | int |  |
| `victimTeamfightDamageDealt[].basic` | 72.6% | 292,508 | 0.0% | bool | PARTIAL |
| `victimTeamfightDamageDealt[].magicDamage` | 72.6% | 292,508 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageDealt[].name` | 72.6% | 292,508 | 0.0% | str | PARTIAL |
| `victimTeamfightDamageDealt[].participantId` | 72.6% | 292,508 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageDealt[].physicalDamage` | 72.6% | 292,508 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageDealt[].spellName` | 72.6% | 292,508 | 0.0% | str | PARTIAL |
| `victimTeamfightDamageDealt[].spellSlot` | 72.6% | 292,508 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageDealt[].trueDamage` | 72.6% | 292,508 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageDealt[].type` | 72.6% | 292,508 | 0.0% | str | PARTIAL |
| `victimTeamfightDamageReceived[].basic` | 72.6% | 521,776 | 0.0% | bool | PARTIAL |
| `victimTeamfightDamageReceived[].magicDamage` | 72.6% | 521,776 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageReceived[].name` | 72.6% | 521,776 | 0.0% | str | PARTIAL |
| `victimTeamfightDamageReceived[].participantId` | 72.6% | 521,776 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageReceived[].physicalDamage` | 72.6% | 521,776 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageReceived[].spellName` | 72.6% | 521,776 | 0.0% | str | PARTIAL |
| `victimTeamfightDamageReceived[].spellSlot` | 72.6% | 521,776 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageReceived[].trueDamage` | 72.6% | 521,776 | 0.0% | int | PARTIAL |
| `victimTeamfightDamageReceived[].type` | 72.6% | 521,776 | 0.0% | str | PARTIAL |

#### `CHAMPION_SPECIAL_KILL`

Present in 820 of 825 matches (99.4%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `killType` | 100.0% | 8,294 | 0.0% | str |  |
| `killerId` | 100.0% | 8,294 | 0.0% | int |  |
| `multiKillLength` | 98.4% | 6,441 | 0.0% | int | PARTIAL |
| `position.x` | 100.0% | 8,294 | 0.0% | int |  |
| `position.y` | 100.0% | 8,294 | 0.0% | int |  |
| `timestamp` | 100.0% | 8,294 | 0.0% | int |  |
| `type` | 100.0% | 8,294 | 0.0% | str |  |

#### `CHAMPION_TRANSFORM`

Present in 36 of 825 matches (4.4%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `participantId` | 100.0% | 37 | 0.0% | int |  |
| `timestamp` | 100.0% | 37 | 0.0% | int |  |
| `transformType` | 100.0% | 37 | 0.0% | str |  |
| `type` | 100.0% | 37 | 0.0% | str |  |

#### `DRAGON_SOUL_GIVEN`

Present in 800 of 825 matches (97.0%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `name` | 100.0% | 1,067 | 0.0% | str |  |
| `teamId` | 100.0% | 1,067 | 0.0% | int |  |
| `timestamp` | 100.0% | 1,067 | 0.0% | int |  |
| `type` | 100.0% | 1,067 | 0.0% | str |  |

#### `ELITE_MONSTER_KILL`

Present in 811 of 825 matches (98.3%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `assistingParticipantIds[]` | 99.4% | 11,868 | 0.0% | int |  |
| `bounty` | 100.0% | 7,569 | 0.0% | int |  |
| `killerId` | 100.0% | 7,569 | 0.0% | int |  |
| `killerTeamId` | 100.0% | 7,569 | 0.0% | int |  |
| `monsterSubType` | 99.9% | 3,349 | 0.0% | str |  |
| `monsterType` | 100.0% | 7,569 | 0.0% | str |  |
| `position.x` | 100.0% | 7,569 | 0.0% | int |  |
| `position.y` | 100.0% | 7,569 | 0.0% | int |  |
| `timestamp` | 100.0% | 7,569 | 0.0% | int |  |
| `type` | 100.0% | 7,569 | 0.0% | str |  |

#### `FEAT_UPDATE`

Present in 126 of 825 matches (15.3%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `featType` | 100.0% | 1,311 | 0.0% | int |  |
| `featValue` | 100.0% | 1,311 | 0.0% | int |  |
| `teamId` | 100.0% | 1,311 | 0.0% | int |  |
| `timestamp` | 100.0% | 1,311 | 0.0% | int |  |
| `type` | 100.0% | 1,311 | 0.0% | str |  |

#### `GAME_END`

Present in 825 of 825 matches (100.0%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `gameId` | 100.0% | 825 | 0.0% | int |  |
| `realTimestamp` | 100.0% | 825 | 0.0% | int |  |
| `timestamp` | 100.0% | 825 | 0.0% | int |  |
| `type` | 100.0% | 825 | 0.0% | str |  |
| `winningTeam` | 100.0% | 825 | 0.0% | int |  |

#### `ITEM_DESTROYED`

Present in 821 of 825 matches (99.5%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `itemId` | 100.0% | 190,840 | 0.0% | int |  |
| `participantId` | 100.0% | 190,840 | 0.0% | int |  |
| `timestamp` | 100.0% | 190,840 | 0.0% | int |  |
| `type` | 100.0% | 190,840 | 0.0% | str |  |

#### `ITEM_PURCHASED`

Present in 825 of 825 matches (100.0%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `itemId` | 100.0% | 203,335 | 0.0% | int |  |
| `participantId` | 100.0% | 203,335 | 0.0% | int |  |
| `timestamp` | 100.0% | 203,335 | 0.0% | int |  |
| `type` | 100.0% | 203,335 | 0.0% | str |  |

#### `ITEM_SOLD`

Present in 803 of 825 matches (97.3%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `itemId` | 100.0% | 8,706 | 0.0% | int |  |
| `participantId` | 100.0% | 8,706 | 0.0% | int |  |
| `timestamp` | 100.0% | 8,706 | 0.0% | int |  |
| `type` | 100.0% | 8,706 | 0.0% | str |  |

#### `ITEM_UNDO`

Present in 820 of 825 matches (99.4%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `afterId` | 100.0% | 10,070 | 0.0% | int |  |
| `beforeId` | 100.0% | 10,070 | 0.0% | int |  |
| `goldGain` | 100.0% | 10,070 | 0.0% | int |  |
| `participantId` | 100.0% | 10,070 | 0.0% | int |  |
| `timestamp` | 100.0% | 10,070 | 0.0% | int |  |
| `type` | 100.0% | 10,070 | 0.0% | str |  |

#### `LEVEL_UP`

Present in 822 of 825 matches (99.6%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `level` | 100.0% | 115,269 | 0.0% | int |  |
| `participantId` | 100.0% | 115,269 | 0.0% | int |  |
| `timestamp` | 100.0% | 115,269 | 0.0% | int |  |
| `type` | 100.0% | 115,269 | 0.0% | str |  |

#### `OBJECTIVE_BOUNTY_FINISH`

Present in 280 of 825 matches (33.9%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `teamId` | 100.0% | 374 | 0.0% | int |  |
| `timestamp` | 100.0% | 374 | 0.0% | int |  |
| `type` | 100.0% | 374 | 0.0% | str |  |

#### `OBJECTIVE_BOUNTY_PRESTART`

Present in 636 of 825 matches (77.1%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `actualStartTime` | 100.0% | 900 | 0.0% | int |  |
| `teamId` | 100.0% | 900 | 0.0% | int |  |
| `timestamp` | 100.0% | 900 | 0.0% | int |  |
| `type` | 100.0% | 900 | 0.0% | str |  |

#### `PAUSE_END`

Present in 825 of 825 matches (100.0%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `realTimestamp` | 100.0% | 825 | 0.0% | int |  |
| `timestamp` | 100.0% | 825 | 0.0% | int |  |
| `type` | 100.0% | 825 | 0.0% | str |  |

#### `SKILL_LEVEL_UP`

Present in 825 of 825 matches (100.0%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `levelUpType` | 100.0% | 125,098 | 0.0% | str |  |
| `participantId` | 100.0% | 125,098 | 0.0% | int |  |
| `skillSlot` | 100.0% | 125,098 | 0.0% | int |  |
| `timestamp` | 100.0% | 125,098 | 0.0% | int |  |
| `type` | 100.0% | 125,098 | 0.0% | str |  |

#### `TURRET_PLATE_DESTROYED`

Present in 812 of 825 matches (98.4%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `killerId` | 100.0% | 39,991 | 0.0% | int |  |
| `laneType` | 100.0% | 39,991 | 0.0% | str |  |
| `position.x` | 100.0% | 39,991 | 0.0% | int |  |
| `position.y` | 100.0% | 39,991 | 0.0% | int |  |
| `teamId` | 100.0% | 39,991 | 0.0% | int |  |
| `timestamp` | 100.0% | 39,991 | 0.0% | int |  |
| `type` | 100.0% | 39,991 | 0.0% | str |  |

#### `WARD_KILL`

Present in 814 of 825 matches (98.7%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `killerId` | 100.0% | 38,367 | 0.0% | int |  |
| `timestamp` | 100.0% | 38,367 | 0.0% | int |  |
| `type` | 100.0% | 38,367 | 0.0% | str |  |
| `wardType` | 100.0% | 38,367 | 0.0% | str |  |

#### `WARD_PLACED`

Present in 825 of 825 matches (100.0%).

| Path | Present in | Occurrences | Null rate | Types | Flags |
|---|---|---|---|---|---|
| `creatorId` | 100.0% | 167,420 | 0.0% | int |  |
| `timestamp` | 100.0% | 167,420 | 0.0% | int |  |
| `type` | 100.0% | 167,420 | 0.0% | str |  |
| `wardType` | 100.0% | 167,420 | 0.0% | str |  |

---

## 4. Concept classification (A / B / C)

**Not yet written.** The A/B/C classification applies to the *concepts the project needs* -- recall timing, wave state, roam, lane pressure -- not to raw API paths, which are directly available by definition and inventoried in section 3.

It also cannot live here: this file is generated, and a concept classification is a hand-written judgement against a candidate catalogue. Mixing the two would mean either losing the judgements on every re-run or freezing the generated half.

Concept classification therefore lives in `docs/ANALYSIS_SPEC.md`, which cites the measurements in this file. This file stays the sole home for *what the telemetry observes*; that file is the sole home for *what we can therefore operationalize*.

