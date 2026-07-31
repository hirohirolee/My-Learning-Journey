import { MIRACLE_DATABASE } from './miracle-data.js?v=3';
import { godProgression } from '../meta/progression.js?v=3';

/**
 * 神力魔法施放與物理破壞執行器 (Miracle Caster & Physics Engine)
 * 處理能量扣除、音效與粒子觸發、對村民與村莊的傷害/治療、以及神獸的觀察模仿
 */
export class MiracleCaster {
    constructor(particleEngine, soundEngine) {
        this.particleEngine = particleEngine;
        this.soundEngine = soundEngine;
    }

    /**
     * 執行施放神力
     */
    castMiracle(spellId, startX, startY, targetX, targetY, isPlayerCast = true, casterRef = null, worldContext = null) {
        const spell = MIRACLE_DATABASE[spellId];
        if (!spell) return false;

        // 1. 玩家施法能量檢查與扣除 (若在自由沙盒模式則不扣能量)
        if (isPlayerCast && worldContext && !worldContext.isSandbox) {
            if (worldContext.energy < spell.cost) {
                if (worldContext.showNotice) worldContext.showNotice('⚡ 祭壇能量不足！請招募村民祈禱或進行獻祭！', 'error');
                return false;
            }
            worldContext.energy -= spell.cost;
        }

        // 2. 觸發施法者或神獸的觀察學習 (結合御獸系學習速度天賦)
        if (isPlayerCast && worldContext && worldContext.creature) {
            const distToCreature = Math.hypot(worldContext.creature.x - targetX, worldContext.creature.y - targetY);
            if (distToCreature < 500) {
                worldContext.creature.observeMiracle(spellId, spell.name);
            }
        }

        // 3. 上帝善惡度變動
        if (isPlayerCast && worldContext) {
            worldContext.godAlignment = Math.max(-100, Math.min(100, worldContext.godAlignment + spell.align));
            if (worldContext.updateGodTheme) worldContext.updateGodTheme(worldContext.godAlignment);
        }

        // 4. 根據神力類別執行對應的實體破壞、資源生成或護盾效果
        this.executeSpellEffect(spell, startX, startY, targetX, targetY, worldContext);

        return true;
    }

    executeSpellEffect(spell, startX, startY, targetX, targetY, world) {
        const pe = this.particleEngine;
        const se = this.soundEngine;
        const dmgMult = godProgression.getBonus('destruction_dmg'); // 毀滅風暴天賦倍率

        switch (spell.id) {
            // ----- 善性神力 -----
            case 'food_1':
            case 'food_2':
                if (se) se.playHeal(targetX, world?.camera?.x);
                if (pe) pe.emitHeal(targetX, targetY, 80, spell.id === 'food_2' ? 3 : 1);
                this.affectVillages(targetX, targetY, 250, world, (v) => {
                    v.food += spell.id === 'food_2' ? 350 : 150;
                    v.addBelief(spell.id === 'food_2' ? 25 : 10, true);
                });
                break;

            case 'wood_1':
                if (se) se.playHeal(targetX, world?.camera?.x);
                if (pe) pe.emitHeal(targetX, targetY, 60, 1);
                this.affectVillages(targetX, targetY, 250, world, (v) => {
                    v.wood += 200;
                    v.addBelief(10, true);
                });
                break;

            case 'water_1':
            case 'water_2':
                if (se) se.playHeal(targetX, world?.camera?.x);
                if (pe) pe.emitStorm(targetX, targetY, 150, false, false, spell.id === 'water_2' ? 15 : 6);
                this.affectVillages(targetX, targetY, 300, world, (v) => {
                    v.food += spell.id === 'water_2' ? 100 : 40;
                    v.addBelief(spell.id === 'water_2' ? 15 : 8, true);
                });
                this.affectVillagers(targetX, targetY, 200, world, (vg) => vg.receiveMiracleImpact(true, 10));
                break;

            case 'forest_1':
                if (se) se.playHeal(targetX, world?.camera?.x);
                if (pe) pe.emitHeal(targetX, targetY, 120, 2);
                if (world && world.spawnForest) world.spawnForest(targetX, targetY, 8);
                break;

            case 'heal_1':
            case 'heal_2':
            case 'heal_3':
                if (se) se.playHeal(targetX, world?.camera?.x);
                const hLevel = spell.id === 'heal_3' ? 3 : (spell.id === 'heal_2' ? 2 : 1);
                if (pe) pe.emitHeal(targetX, targetY, hLevel * 100, hLevel);
                this.affectVillagers(targetX, targetY, hLevel * 120, world, (vg) => {
                    vg.isDead = false;
                    vg.receiveMiracleImpact(true, hLevel * 15);
                });
                this.affectVillages(targetX, targetY, hLevel * 150, world, (v) => v.addBelief(hLevel * 12, true));
                if (world && world.creature && Math.hypot(world.creature.x - targetX, world.creature.y - targetY) < hLevel * 120) {
                    world.creature.health = Math.min(100, world.creature.health + hLevel * 30);
                }
                break;

            // ----- 惡性神力 (結合毀滅系傷害加成) -----
            case 'fireball_1':
            case 'fireball_2':
            case 'fireball_3':
                if (se) se.playFireball(targetX, world?.camera?.x);
                const fbCount = spell.id === 'fireball_3' ? 8 : (spell.id === 'fireball_2' ? 3 : 1);
                if (pe) {
                    pe.emitFireball(startX, startY, targetX, targetY, fbCount, (ix, iy) => {
                        if (se) se.playThunder(ix, world?.camera?.x);
                        this.applyDestructiveImpact(ix, iy, 100 * (fbCount > 1 ? 1.5 : 1) * dmgMult, world, true);
                    });
                }
                break;

            case 'lightning_1':
            case 'lightning_2':
            case 'lightning_3':
                if (se) se.playThunder(targetX, world?.camera?.x);
                const lInt = spell.id === 'lightning_3' ? 3 : (spell.id === 'lightning_2' ? 2 : 1);
                if (pe) pe.emitLightning(targetX, targetY, lInt, (ix, iy) => {
                    this.applyDestructiveImpact(ix, iy, 80 * lInt * dmgMult, world, true);
                });
                if (world && world.triggerFlash) world.triggerFlash();
                break;

            case 'storm_1':
            case 'storm_2':
            case 'storm_3':
                if (se) se.playThunder(targetX, world?.camera?.x);
                const hasL = spell.id !== 'storm_1';
                const hasT = spell.id === 'storm_3';
                if (pe) pe.emitStorm(targetX, targetY, 200 * dmgMult, hasL, hasT, hasT ? 15 : 10);
                this.affectVillages(targetX, targetY, 250 * dmgMult, world, (v) => {
                    v.takeDamage((hasT ? 150 : 50) * dmgMult, pe);
                    v.addBelief((hasT ? 25 : 10) * godProgression.getBonus('fear_mult'), false);
                });
                this.affectVillagers(targetX, targetY, 200 * dmgMult, world, (vg) => vg.receiveMiracleImpact(false, 15));
                break;

            case 'blast_1':
            case 'blast_2':
            case 'blast_3':
                if (se) se.playThunder(targetX, world?.camera?.x);
                const bRad = (spell.id === 'blast_3' ? 250 : (spell.id === 'blast_2' ? 160 : 100)) * dmgMult;
                if (pe) pe.emitExplosion(targetX, targetY, bRad, '#f97316');
                this.applyDestructiveImpact(targetX, targetY, bRad, world, true);
                if (world && world.triggerFlash) world.triggerFlash();
                break;

            case 'wolf_pack':
                if (se) se.playCreatureRoar(1.5, targetX, world?.camera?.x);
                const rivalV = world ? world.villages.find(v => v.owner !== 'player') : null;
                if (pe) pe.emitWolfPack(targetX, targetY, 8, rivalV);
                if (rivalV) rivalV.addBelief(20 * godProgression.getBonus('fear_mult'), false);
                break;

            // ----- 輔助與其他神力 -----
            case 'other_teleport':
                if (se) se.playHeal(targetX, world?.camera?.x);
                if (pe) pe.emitHeal(targetX, targetY, 100, 2);
                if (world && world.creature) {
                    world.creature.x = targetX;
                    world.creature.y = targetY;
                    world.creature.tetherPoint = { x: targetX, y: targetY };
                    world.creature.thought = '「🌀 傳送神力光環！我來到了指定位置！」';
                }
                break;

            case 'other_flight':
                if (se) se.playSacrifice(targetX, world?.camera?.x);
                const isGoodFlight = world ? world.godAlignment >= 0 : true;
                if (pe) pe.emitMonsterFlight(targetX, targetY, isGoodFlight, 15);
                this.affectVillages(targetX, targetY, 300, world, (v) => v.addBelief(15, isGoodFlight));
                break;

            case 'other_phys_shield':
            case 'other_magic_shield':
                if (se) se.playHeal(targetX, world?.camera?.x);
                const shieldColor = spell.id === 'other_phys_shield' ? 'rgba(251, 191, 36, 0.4)' : 'rgba(168, 85, 247, 0.4)';
                if (pe) {
                    pe.persistentEffects.push({
                        type: 'holy_circle', x: targetX, y: targetY, radius: 180,
                        alpha: 0.9, duration: 25, color: shieldColor
                    });
                }
                break;

            default:
                if (spell.category === 'aux' && world && world.creatureTrainer) {
                    if (se) se.playHeal(world.creature.x, world?.camera?.x);
                    if (pe) pe.emitHeal(world.creature.x, world.creature.y, 80, 2);
                    world.creatureTrainer.applyAuxiliaryMiracle(spell.id, 25);
                }
                break;
        }
    }

    applyDestructiveImpact(x, y, radius, world, isEvilAct = true) {
        if (!world) return;
        const fearMult = godProgression.getBonus('fear_mult');
        this.affectResources(x, y, radius, world, (res) => res.takeDamage(100, this.particleEngine));
        this.affectVillages(x, y, radius, world, (v) => {
            v.takeDamage(120, this.particleEngine);
            v.addBelief(20 * fearMult, false); // 恐懼與敬畏的信仰度
        });
        this.affectVillagers(x, y, radius * 0.8, world, (vg) => vg.receiveMiracleImpact(false, 25));
    }

    affectVillages(x, y, radius, world, cb) {
        if (!world || !world.villages) return;
        for (const v of world.villages) {
            if (Math.hypot(v.x - x, v.y - y) <= radius) cb(v);
        }
    }

    affectVillagers(x, y, radius, world, cb) {
        if (!world || !world.villagers) return;
        for (const vg of world.villagers) {
            if (Math.hypot(vg.x - x, vg.y - y) <= radius) cb(vg);
        }
    }

    affectResources(x, y, radius, world, cb) {
        if (!world || !world.resources) return;
        for (const res of world.resources) {
            if (Math.hypot(res.x - x, res.y - y) <= radius) cb(res);
        }
    }
}
