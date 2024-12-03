import subprocess
import os
from datetime import timedelta
from typing import List
import typer

app = typer.Typer()


class Job:
    def __init__(
        self,
        uuid_job_id,
        slurm_job_id=None,
        status=None,
        url=None,
        port=None,
        host=None,
        running_time=timedelta(seconds=0),
    ):
        self.uuid_job_id = uuid_job_id
        self.slurm_job_id = slurm_job_id
        self.status = status
        self.url = url
        self.port = port
        self.host = host
        self.running_time = running_time

    def __repr__(self):
        return f"Job(uuid={self.uuid_job_id}, slurm_id={self.slurm_job_id}, status={self.status}, running_time={self.running_time}, url={self.url}, host={self.host}, port={self.port})"

    def to_dict(self):
        return {
            "uuid_job_id": self.uuid_job_id,
            "slurm_job_id": self.slurm_job_id,
            "status": self.status,
            "url": self.url,
            "port": self.port,
            "host": self.host,
            "running_time": str(self.running_time),
        }


def get_slurm_jobs(jobs: List[Job]):
    river_home = os.getenv("RIVER_HOME")
    if not river_home:
        raise EnvironmentError("RIVER_HOME environment variable is not set")

    for job in jobs:
        if not job.slurm_job_id:
            try:
                job_path = f"{river_home}/.river/jobs/{job.uuid_job_id}"
                if os.path.exists(f"{job_path}/job.id"):
                    slurm_id = subprocess.check_output(
                        f"cat {job_path}/job.id", shell=True
                    )
                    job.slurm_job_id = slurm_id.decode().strip()
                if os.path.exists(f"{job_path}/job.url"):
                    slurm_url = subprocess.check_output(
                        f"cat {job_path}/job.url", shell=True
                    )
                    job.url = slurm_url.decode().strip()
                if os.path.exists(f"{job_path}/job.port"):
                    slurm_port = subprocess.check_output(
                        f"cat {job_path}/job.port", shell=True
                    )
                    job.port = slurm_port.decode().strip()
                if os.path.exists(f"{job_path}/job.host"):
                    slurm_host = subprocess.check_output(
                        f"cat {job_path}/job.host", shell=True
                    )
                    job.host = slurm_host.decode().strip()
            except subprocess.CalledProcessError:
                pass


def parse_duration(duration_str):
    if "-" in duration_str:
        days, time = duration_str.split("-")
        total_seconds = 0
        if days:
            total_seconds += int(days) * 24 * 3600
        hours, minutes, seconds = map(int, time.split(":"))
        total_seconds += hours * 3600 + minutes * 60 + seconds
    elif ":" in duration_str:
        parts = duration_str.split(":")
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            total_seconds = minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            total_seconds = hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"Invalid duration format: {duration_str}")
    else:
        total_seconds = int(duration_str)
    return timedelta(seconds=total_seconds)


def parsing_squeue_status(jobs: List[Job], states: str, command="squeue"):
    if states:
        lines = states.split("\n")[1:-1]
        for line in lines:
            for job in jobs:
                if job.slurm_job_id == line.split()[0]:
                    job_id, state, time = line.split()
                    job.running_time = parse_duration(time)
                    job.status = state


def get_jobs_info(jobs: List[Job]):
    get_slurm_jobs(jobs)
    job_ids = [job.slurm_job_id for job in jobs if job.slurm_job_id]
    if len(job_ids) == 0:
        return
    job_ids = ",".join(job_ids)
    squeue_cmd = f"squeue --jobs {job_ids} --format='%.18i %.9T %.10M'"
    sacct_cmd = f"sacct --jobs {job_ids} --format='JobID,State,Elapsed'"
    try:
        squeue_status = subprocess.check_output(squeue_cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        squeue_status = None
    try:
        sacct_status = subprocess.check_output(sacct_cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError:
        sacct_status = None
    parsing_squeue_status(jobs, sacct_status, command="sacct")
    parsing_squeue_status(jobs, squeue_status)


@app.command()
def info(uuid_job_ids: List[str]):
    """Fetch and display information about jobs."""
    jobs = [Job(uuid_job_id=uuid) for uuid in uuid_job_ids]
    get_jobs_info(jobs)
    for job in jobs:
        typer.echo(job.to_dict())


if __name__ == "__main__":
    app()