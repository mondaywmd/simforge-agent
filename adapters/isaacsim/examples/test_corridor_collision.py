"""Floor raycast, forward movement and wall-blocking test at the documented corridor spawn.
Run in Isaac Sim 6.1 Script Editor, not system Python.
Requires this project’s USD scenes and /World/NavBot prim hierarchy.
Outputs are relative to the project containing isaacsim/scenes/.
"""
import asyncio

async def main():
    import carb
    import omni.usd
    from pathlib import Path
    stage_check = omni.usd.get_context().get_stage()
    assert stage_check and not stage_check.GetRootLayer().anonymous, 'Open the saved test scene first.'
    settings = carb.settings.get_settings()
    assert settings.get('/app/asyncRendering') is False, 'Use the synchronous-rendering launcher.'
    assert settings.get('/exts/isaacsim.core.throttling/enable_async') is False, 'Disable automatic async toggle.'
    assert stage_check.GetEndTimeCode() / stage_check.GetTimeCodesPerSecond() > 20, 'Set a sufficient timeline range.'
    root = Path(stage_check.GetRootLayer().realPath).parents[2]
    import json, math
    from pathlib import Path
    import carb, omni.usd, omni.timeline, omni.kit.app, omni.physx
    from pxr import UsdGeom, UsdPhysics
    from omni.physics.tensors import create_simulation_view
    ctx=omni.usd.get_context(); stage=ctx.get_stage()
    assert stage.GetRootLayer().identifier.endswith('navbot_corridor_test.usda')
    assert carb.settings.get_settings().get('/app/asyncRendering') is False
    t=omni.timeline.get_timeline_interface()
    assert t.is_stopped()
    drives=[UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath('/World/NavBot/Physics/'+n),'angular') for n in ['wheel_left_joint','wheel_right_joint']]
    rotation=stage.GetPrimAtPath('/World/NavBot').GetAttribute('xformOp:rotateZ')
    async def frames(n):
        for _ in range(n): await omni.kit.app.get_app().next_update_async()
    async def sim_second():
        deadline=t.get_current_time()+1
        for _ in range(600):
            await frames(1)
            if t.get_current_time()>=deadline: return
        raise RuntimeError('Simulation time stalled')
    def speed(value):
        for d in drives: d.GetTargetVelocityAttr().Set(math.degrees(value))
    def position(body): return body.get_transforms().copy()[0,:3].tolist()
    results=[]
    try:
        for name,yaw,seconds in [('forward',90,4),('wall_stop',0,10)]:
            rotation.Set(yaw);speed(0)
            t.play();t.commit();await frames(120)
            sim=create_simulation_view('numpy',stage_id=ctx.get_stage_id())
            body=sim.create_rigid_body_view('/World/NavBot/Geometry/base_footprint/base_link')
            start=position(body)
            q=omni.physx.get_physx_scene_query_interface()
            floor=q.raycast_closest((-.55,-3,.5),(0,0,-1),1)
            floor_info={'hit':floor['hit'],'collision':floor.get('collision'),'position':list(floor['position']) if floor['hit'] else None}
            assert floor['hit'] and floor['collision'].endswith('/Floor'),floor_info
            assert abs(start[2]-.01)<.02,start
            speed(3)
            sim_start=t.get_current_time()
            samples=[]
            for _ in range(seconds):
                await sim_second();samples.append(position(body))
                assert -.04<samples[-1][2]<.12,'Robot left floor'
            elapsed=t.get_current_time()-sim_start
            speed(0);await sim_second()
            final=position(body)
            passed=(final[1]-start[1]>.25 and abs(final[0]-start[0])<.08) if name=='forward' else (final[0]-start[0]>.2 and final[0]<.247 and math.dist(samples[-1],samples[-2])<.01)
            results.append({'test':name,'duration_sim_s':elapsed,'start':start,'samples_1s':samples,'after_braking':final,'floor_query':floor_info,'passed':passed})
            del body,sim
            t.stop();t.commit();await frames(60)
    finally:
        speed(0);t.stop();t.commit();await frames(30)
        rotation.Set(90)
        # No automatic save of the scene.
        dest=root/'tests/physics/robot_corridor'
        dest.mkdir(parents=True,exist_ok=True)
        (dest/'motion_report.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results,indent=2))
    assert len(results)==2 and all(r['passed'] for r in results)


if globals().get('_NAVBOT_TASK') is not None and not _NAVBOT_TASK.done():
    raise RuntimeError('A NavBot script is still running. Wait for completion.')
_NAVBOT_TASK = asyncio.ensure_future(main())
def _report_done(task):
    if not task.cancelled() and task.exception():
        import traceback
        traceback.print_exception(type(task.exception()), task.exception(), task.exception().__traceback__)
_NAVBOT_TASK.add_done_callback(_report_done)
