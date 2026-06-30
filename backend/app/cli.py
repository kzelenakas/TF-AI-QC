"""TF AI-QC Admin CLI

Usage:
  python -m app.cli create-admin --email admin@truefootage.com --bubble-id <id>
  python -m app.cli seed-rules
  python -m app.cli check-health
  python -m app.cli list-rules
  python -m app.cli toggle-rule UAD-004 --enable
  python -m app.cli toggle-rule FNMA-001 --disable
"""
from __future__ import annotations
import sys
import click
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models.user import User, UserRole


@click.group()
def cli():
    """TF AI-QC Admin CLI"""


@cli.command()
@click.option("--email", required=True)
@click.option("--bubble-id", required=True)
@click.option("--name", default="Admin")
def create_admin(email: str, bubble_id: str, name: str):
    """Create or promote a user to admin role."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.bubble_user_id == bubble_id).first()
        if user:
            user.role = UserRole.admin
            user.email = email
            user.name = name
            user.is_active = True
        else:
            user = User(bubble_user_id=bubble_id, email=email, name=name, role=UserRole.admin, is_active=True)
            db.add(user)
        db.commit()
        click.echo(f"✓ Admin user ready: {email} (bubble_id={bubble_id})")
    except Exception as e:
        db.rollback()
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@cli.command()
def seed_rules():
    """Seed the rules table (upsert, safe to re-run)."""
    db = SessionLocal()
    try:
        from app.db.seed_rules import seed
        seed(db)
        click.echo("✓ Rules seeded.")
    except Exception as e:
        db.rollback()
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


@cli.command()
def check_health():
    """Verify DB connectivity."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        click.echo("✓ Database: connected")
    except Exception as e:
        click.echo(f"✗ Database: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()
    db = SessionLocal()
    try:
        from app.models.report import Report
        from app.models.rule import Rule
        click.echo(f"✓ Reports: {db.query(Report).count()}")
        rules = db.query(Rule)
        click.echo(f"✓ Rules: {rules.count()} total, {rules.filter(Rule.enabled.is_(True)).count()} enabled")
    finally:
        db.close()


@cli.command()
def list_rules():
    """Print all rules with enabled state."""
    db = SessionLocal()
    try:
        from app.models.rule import Rule
        rules = db.query(Rule).order_by(Rule.category, Rule.code).all()
        if not rules:
            click.echo("No rules. Run: python -m app.cli seed-rules")
            return
        click.echo(f"{'CODE':<20} {'CAT':<12} {'SEV':<10} {'ON':<4} DESCRIPTION")
        click.echo("-" * 72)
        for r in rules:
            click.echo(f"{r.code:<20} {r.category.value:<12} {r.severity:<10} {'Y' if r.enabled else 'N':<4} {r.description[:40]}")
    finally:
        db.close()


@cli.command()
@click.argument("rule_code")
@click.option("--enable/--disable", required=True)
def toggle_rule(rule_code: str, enable: bool):
    """Enable or disable a rule by code."""
    db = SessionLocal()
    try:
        from app.models.rule import Rule
        from app.services.rules.engine import get_engine
        r = db.query(Rule).filter(Rule.code == rule_code).first()
        if not r:
            click.echo(f"✗ Rule '{rule_code}' not found.", err=True)
            sys.exit(1)
        r.enabled = enable
        db.commit()
        get_engine().invalidate_cache()
        click.echo(f"✓ Rule {rule_code} {'enabled' if enable else 'disabled'}.")
    except Exception as e:
        db.rollback()
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    cli()
