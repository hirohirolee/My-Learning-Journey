import dataclasses
import json
import os
import re
from datetime import datetime

import pandas as pd

from config import config
from core.plugin_registry import BaseExporter, registry
from exceptions import ExportException
from models import Post


def _generate_run_id(posts: list[Post]) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not posts:
        return f"export_{timestamp}"
    if len(posts) == 1 and posts[0].title:
        clean_title = re.sub(r'[\\/*?:"<>|]', "", posts[0].title).strip()
        clean_title = re.sub(r'\s+', "_", clean_title)
        if clean_title:
            return f"{clean_title}_{timestamp}"
    else:
        titles = [re.sub(r'[\\/*?:"<>|]', "", p.title).strip() for p in posts if p.title]
        titles = [t for t in titles if t]
        if titles:
            prefix = "_".join(titles[:2])
            if len(titles) > 2:
                prefix += f"等{len(titles)}店"
            return f"{prefix}_{timestamp}"
    return f"export_{timestamp}"


class JSONExporter(BaseExporter):
    def export(self, posts: list[Post], output_dir: str, run_id: str | None = None) -> None:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, "export.json")
        try:
            data = [dataclasses.asdict(p) for p in posts]
            # Convert datetime to string
            for item in data:
                item["created_at"] = (
                    item["created_at"].isoformat() if item["created_at"] else None
                )
                item["fetched_at"] = (
                    item["fetched_at"].isoformat() if item["fetched_at"] else None
                )
                for c in item["comments"]:
                    c["created_at"] = (
                        c["created_at"].isoformat() if c["created_at"] else None
                    )

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            if run_id:
                hist_filename = os.path.join(output_dir, f"{run_id}.json")
                with open(hist_filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ExportException(f"Failed to export to JSON: {e}")


class CSVExporter(BaseExporter):
    def export(self, posts: list[Post], output_dir: str, run_id: str | None = None) -> None:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, "export.csv")
        comments_filename = os.path.join(output_dir, "export_comments.csv")
        try:
            data = []
            comments_data = []
            for p in posts:
                data.append(
                    {
                        "id": p.id,
                        "forum": p.forum_name,
                        "url": p.url,
                        "title": p.title,
                        "author": p.author,
                        "content_preview": p.content[:100].replace("\n", " "),
                        "comments_count": len(p.comments),
                        "created_at": p.created_at,
                        "rating": p.rating,
                    }
                )
                for c in p.comments:
                    comments_data.append(
                        {
                            "post_id": p.id,
                            "post_title": p.title,
                            "comment_id": c.id,
                            "author": c.author,
                            "content": c.content,
                            "rating": c.rating,
                            "created_at": c.created_at,
                        }
                    )
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            if run_id:
                df.to_csv(os.path.join(output_dir, f"{run_id}.csv"), index=False, encoding="utf-8-sig")
            
            if comments_data:
                cdf = pd.DataFrame(comments_data)
                cdf.to_csv(comments_filename, index=False, encoding="utf-8-sig")
                if run_id:
                    cdf.to_csv(os.path.join(output_dir, f"{run_id}_comments.csv"), index=False, encoding="utf-8-sig")
        except Exception as e:
            raise ExportException(f"Failed to export to CSV: {e}")


class ExcelExporter(BaseExporter):
    def export(self, posts: list[Post], output_dir: str, run_id: str | None = None) -> None:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, "export.xlsx")
        try:
            posts_data = []
            comments_data = []
            for p in posts:
                posts_data.append({
                    "id": p.id,
                    "forum": p.forum_name,
                    "url": p.url,
                    "title": p.title,
                    "author": p.author,
                    "content_preview": p.content[:100].replace("\n", " "),
                    "comments_count": len(p.comments),
                    "created_at": p.created_at.replace(tzinfo=None) if p.created_at else None,
                    "rating": p.rating,
                })
                for c in p.comments:
                    comments_data.append({
                        "post_id": p.id,
                        "post_title": p.title,
                        "comment_id": c.id,
                        "author": c.author,
                        "content": c.content,
                        "rating": c.rating,
                        "created_at": c.created_at.replace(tzinfo=None) if c.created_at else None
                    })
                    
            def _write_excel(path: str):
                with pd.ExcelWriter(path, engine='openpyxl') as writer:
                    if comments_data:
                        pd.DataFrame(comments_data).to_excel(writer, sheet_name="Comments", index=False)
                    pd.DataFrame(posts_data).to_excel(writer, sheet_name="Posts", index=False)
                    if not comments_data:
                        pd.DataFrame([{"info": "No comments found"}]).to_excel(writer, sheet_name="Comments", index=False)

            _write_excel(filename)
            if run_id:
                _write_excel(os.path.join(output_dir, f"{run_id}.xlsx"))
        except Exception as e:
            raise ExportException(f"Failed to export to Excel: {e}")


class ExporterPipeline:
    def __init__(self) -> None:
        registry.register_exporter("json", JSONExporter)
        registry.register_exporter("csv", CSVExporter)
        registry.register_exporter("excel", ExcelExporter)

    def export(self, posts: list[Post]) -> None:
        run_id = _generate_run_id(posts)
        for fmt in config.export.formats:
            exporter_cls = registry.get_exporter(fmt)
            if exporter_cls:
                exporter = exporter_cls()
                exporter.export(posts, config.export.output_dir, run_id=run_id)
            else:
                raise ExportException(f"Unsupported export format: {fmt}")
