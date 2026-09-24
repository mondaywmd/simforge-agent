"""Forward, turn and brake tests on the flat NavBot scene. Records measured poses.
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
    """Execute in Isaac Sim Python Server. Differential-drive smoke test, no ROS/RL."""
    import json
    import math
    from pathlib import Path
    import omni.usd
    import omni.kit.app
    import omni.timeline
    from pxr import UsdPhysics
    from omni.physics.tensors import create_simulation_view


    ctx=omni.usd.get_context()
    timeline=omni.timeline.get_timeline_interface()
    if not timeline.is_stopped():
        timeline.stop(); timeline.commit()
        for _ in range(10): await omni.kit.app.get_app().next_update_async()
    stage=ctx.get_stage()
    if not stage or not stage.GetPrimAtPath('/World/NavBot/Physics/wheel_left_joint'):
        raise RuntimeError('Open the NavBot robot test scene first.')
    assert Path(stage.GetRootLayer().realPath).name == 'navbot_drive_test.usda', 'Open the flat drive-test scene.'
    from omni.kit.viewport.utility import get_active_viewport
    get_active_viewport().set_active_camera('/World/Camera')
    drives=[UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath('/World/NavBot/Physics/'+name),'angular')
            for name in ('wheel_left_joint','wheel_right_joint')]
    for drive in drives:
        assert drive
        drive.CreateTargetVelocityAttr(0.0)
        drive.CreateStiffnessAttr(0.0)
    # Keep the importer's damping and original force limits.
    # Scene edits stay in memory; no automatic scene save.

    async def frames(count):
        for _ in range(count): await omni.kit.app.get_app().next_update_async()

    async def sim_seconds(seconds):
        end = timeline.get_current_time() + seconds
        for _ in range(int(seconds * 600)):
            await frames(1)
            if timeline.get_current_time() >= end:
                return
        raise RuntimeError('Simulation time did not advance as expected.')

    def targets(left,right):
        for drive,value in zip(drives,(left,right)):
            drive.GetTargetVelocityAttr().Set(math.degrees(value))

    def pose(view):
        values=view.get_transforms().copy()[0].tolist()
        assert all(math.isfinite(x) for x in values)
        x,y,z,w=values[3:7]
        yaw=math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
        return {'position':values[:3],'quaternion_xyzw':values[3:7],'yaw_rad':yaw}

    results=[]
    try:
        for name,left,right in [('forward',3.0,3.0),('turn_left',-2.0,2.0)]:
            targets(0,0)
            timeline.play(); timeline.commit()
            await frames(60)
            sim=create_simulation_view('numpy',stage_id=ctx.get_stage_id())
            body=sim.create_rigid_body_view('/World/NavBot/Geometry/base_footprint/base_link')
            before=pose(body)
            start=timeline.get_current_time()
            targets(left,right)
            await sim_seconds(3)
            after=pose(body)
            elapsed=timeline.get_current_time()-start
            targets(0,0)
            await frames(60)
            stopped=pose(body)
            distance=math.hypot(after['position'][0]-before['position'][0],after['position'][1]-before['position'][1])
            angle=math.atan2(math.sin(after['yaw_rad']-before['yaw_rad']),math.cos(after['yaw_rad']-before['yaw_rad']))
            result={'test':name,'wheel_targets_rad_s':[left,right],'duration_s':elapsed,
                    'before':before,'after':after,'after_braking':stopped,'distance_m':distance,'yaw_change_deg':math.degrees(angle)}
            result['passed']=(distance>0.15 and abs(math.degrees(angle))<15) if name=='forward' else (angle>0.5 and distance<0.1)
            results.append(result)
            del body,sim
            timeline.stop(); timeline.commit()
            await frames(60)
    finally:
        targets(0,0)
        timeline.stop(); timeline.commit()
        await frames(10)
        # Scene edits stay in memory; no automatic scene save.
    report=root/'tests/physics/robot_import/drive_test_report.json'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))
    assert all(item['passed'] for item in results), 'Drive test failed; inspect recorded results.'



if globals().get('_NAVBOT_TASK') is not None and not _NAVBOT_TASK.done():
    raise RuntimeError('A NavBot script is still running. Wait for completion.')
_NAVBOT_TASK = asyncio.ensure_future(main())
def _report_done(task):
    if not task.cancelled() and task.exception():
        import traceback
        traceback.print_exception(type(task.exception()), task.exception(), task.exception().__traceback__)
_NAVBOT_TASK.add_done_callback(_report_done)
