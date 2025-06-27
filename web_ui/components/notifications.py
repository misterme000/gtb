"""
Notification System for Grid Trading Bot Web UI

Provides toast notifications, loading states, and progress indicators
for better user feedback during operations.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from typing import Dict, Any, Optional, List
from enum import Enum


class NotificationType(Enum):
    """Types of notifications."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "danger"
    INFO = "info"
    LOADING = "primary"


class NotificationSystem:
    """Centralized notification system for the web UI."""
    
    @staticmethod
    def create_toast_container():
        """Create an enhanced container for toast notifications."""
        return html.Div(
            id="toast-container",
            children=[],
            style={
                "position": "fixed",
                "top": "20px",
                "right": "20px",
                "z-index": "9999",
                "max-width": "400px",
                "min-width": "300px"
            }
        )

    @staticmethod
    def create_progress_toast(message: str, progress: int = 0, show_progress: bool = True):
        """Create a progress toast notification."""
        return dbc.Toast([
            dbc.ToastHeader([
                html.I(className="fas fa-spinner fa-spin me-2"),
                html.Strong("Processing...", className="me-auto"),
                html.Small(f"{progress}%" if show_progress else "", className="text-muted")
            ]),
            dbc.ToastBody([
                html.P(message, className="mb-2"),
                dbc.Progress(
                    value=progress,
                    striped=True,
                    animated=True,
                    color="primary",
                    className="mb-0"
                ) if show_progress else None
            ])
        ],
        is_open=True,
        dismissible=False,
        duration=0,  # Don't auto-dismiss
        style={"min-width": "300px"}
        )
    
    @staticmethod
    def create_toast(
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        title: Optional[str] = None,
        duration: int = 5000,
        dismissible: bool = True
    ):
        """
        Create a toast notification.
        
        Args:
            message: The notification message
            notification_type: Type of notification (success, warning, error, info)
            title: Optional title for the notification
            duration: Duration in milliseconds (0 for persistent)
            dismissible: Whether the toast can be dismissed
        """
        icon_map = {
            NotificationType.SUCCESS: "fas fa-check-circle",
            NotificationType.WARNING: "fas fa-exclamation-triangle",
            NotificationType.ERROR: "fas fa-times-circle",
            NotificationType.INFO: "fas fa-info-circle",
            NotificationType.LOADING: "fas fa-spinner fa-spin"
        }
        
        header_content = []
        if title:
            header_content.append(
                html.Strong(title, className="me-auto")
            )
        
        if dismissible:
            header_content.append(
                dbc.Button(
                    html.I(className="fas fa-times"),
                    color="link",
                    size="sm",
                    className="btn-close",
                    style={"border": "none", "background": "none"}
                )
            )
        
        # Create toast content with header if provided
        toast_content = []

        if header_content:
            # Create custom header since ToastHeader may not be available
            toast_content.append(
                html.Div(
                    header_content,  # header_content is already a list with title and close button
                    className="toast-header",
                    style={
                        "display": "flex",
                        "justify-content": "space-between",
                        "align-items": "center",
                        "padding": "0.5rem 0.75rem",
                        "background-color": "rgba(0,0,0,0.03)",
                        "border-bottom": "1px solid rgba(0,0,0,0.05)"
                    }
                )
            )

        # Add toast body
        toast_content.append(
            html.Div([
                html.I(className=icon_map[notification_type], style={"margin-right": "8px"}),
                message
            ], className="toast-body", style={"padding": "0.75rem"})
        )

        return dbc.Toast(
            toast_content,
            color=notification_type.value,
            duration=duration,
            dismissable=dismissible,  # Note: parameter is 'dismissable' not 'dismissible'
            style={"margin-bottom": "10px"}
        )
    
    @staticmethod
    def create_loading_spinner(
        size: str = "md",
        color: str = "primary",
        text: Optional[str] = None
    ):
        """
        Create a loading spinner with optional text.
        
        Args:
            size: Size of spinner (sm, md, lg)
            color: Color of spinner
            text: Optional loading text
        """
        spinner_sizes = {
            "sm": {"width": "1rem", "height": "1rem"},
            "md": {"width": "2rem", "height": "2rem"},
            "lg": {"width": "3rem", "height": "3rem"}
        }
        
        spinner = dbc.Spinner(
            color=color,
            size=size,
            style=spinner_sizes.get(size, spinner_sizes["md"])
        )
        
        if text:
            return html.Div([
                spinner,
                html.Div(text, className="mt-2 text-center")
            ], className="text-center")
        
        return html.Div(spinner, className="text-center")
    
    @staticmethod
    def create_progress_bar(
        value: int,
        max_value: int = 100,
        label: Optional[str] = None,
        color: str = "primary",
        striped: bool = False,
        animated: bool = False
    ):
        """
        Create a progress bar.
        
        Args:
            value: Current progress value
            max_value: Maximum value (default 100)
            label: Optional label text
            color: Progress bar color
            striped: Whether to show stripes
            animated: Whether to animate stripes
        """
        percentage = (value / max_value) * 100
        
        progress_bar = dbc.Progress(
            value=percentage,
            color=color,
            striped=striped,
            animated=animated,
            style={"height": "20px"}
        )
        
        if label:
            return html.Div([
                html.Div(label, className="mb-2"),
                progress_bar,
                html.Div(
                    f"{value}/{max_value} ({percentage:.1f}%)",
                    className="mt-1 text-muted small text-center"
                )
            ])
        
        return progress_bar
    
    @staticmethod
    def create_loading_overlay(
        content,
        is_loading: bool = False,
        loading_text: str = "Loading...",
        spinner_size: str = "lg"
    ):
        """
        Create a loading overlay for content.
        
        Args:
            content: The content to overlay
            is_loading: Whether to show loading state
            loading_text: Text to show while loading
            spinner_size: Size of the loading spinner
        """
        if is_loading:
            return html.Div([
                html.Div(
                    content,
                    style={
                        "opacity": "0.3",
                        "pointer-events": "none"
                    }
                ),
                html.Div([
                    NotificationSystem.create_loading_spinner(
                        size=spinner_size,
                        text=loading_text
                    )
                ], style={
                    "position": "absolute",
                    "top": "50%",
                    "left": "50%",
                    "transform": "translate(-50%, -50%)",
                    "z-index": "1000"
                })
            ], style={"position": "relative"})
        
        return content
    
    @staticmethod
    def create_status_indicator(
        status: str,
        message: str,
        details: Optional[List[str]] = None
    ):
        """
        Create a status indicator with message and optional details.
        
        Args:
            status: Status type (success, warning, error, info, loading)
            message: Main status message
            details: Optional list of detail messages
        """
        status_config = {
            "success": {"color": "success", "icon": "fas fa-check-circle"},
            "warning": {"color": "warning", "icon": "fas fa-exclamation-triangle"},
            "error": {"color": "danger", "icon": "fas fa-times-circle"},
            "info": {"color": "info", "icon": "fas fa-info-circle"},
            "loading": {"color": "primary", "icon": "fas fa-spinner fa-spin"}
        }
        
        config = status_config.get(status, status_config["info"])
        
        content = [
            html.Div([
                html.I(className=config["icon"], style={"margin-right": "8px"}),
                html.Strong(message)
            ], className="mb-2")
        ]
        
        if details:
            content.append(
                html.Ul([
                    html.Li(detail) for detail in details
                ], className="mb-0 small")
            )
        
        return dbc.Alert(
            content,
            color=config["color"],
            className="mb-3"
        )
    
    @staticmethod
    def create_operation_feedback(
        operation_name: str,
        is_running: bool = False,
        progress: Optional[int] = None,
        max_progress: Optional[int] = None,
        status_message: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """
        Create comprehensive operation feedback component.
        
        Args:
            operation_name: Name of the operation
            is_running: Whether operation is currently running
            progress: Current progress value
            max_progress: Maximum progress value
            status_message: Current status message
            error_message: Error message if operation failed
        """
        content = []
        
        # Operation header
        header_icon = "fas fa-spinner fa-spin" if is_running else "fas fa-cog"
        content.append(
            html.H6([
                html.I(className=header_icon, style={"margin-right": "8px"}),
                operation_name
            ], className="mb-3")
        )
        
        # Progress bar if progress is provided
        if progress is not None and max_progress is not None:
            content.append(
                NotificationSystem.create_progress_bar(
                    value=progress,
                    max_value=max_progress,
                    label="Progress",
                    animated=is_running
                )
            )
        
        # Status message
        if status_message:
            content.append(
                html.Div([
                    html.I(className="fas fa-info-circle", style={"margin-right": "8px"}),
                    status_message
                ], className="mt-2 text-muted")
            )
        
        # Error message
        if error_message:
            content.append(
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle", style={"margin-right": "8px"}),
                    error_message
                ], color="danger", className="mt-2")
            )
        
        return dbc.Card([
            dbc.CardBody(content)
        ], className="mb-3")


# Global notification system instance
notification_system = NotificationSystem()

# Additional enhanced notification methods
def create_step_indicator(steps: List[str], current_step: int = 0):
    """Create a step indicator for multi-step processes."""
    step_items = []

    for i, step in enumerate(steps):
        is_current = i == current_step
        is_completed = i < current_step

        # Determine step status
        if is_completed:
            icon = "fas fa-check"
            color = "success"
        elif is_current:
            icon = "fas fa-circle"
            color = "primary"
        else:
            icon = "far fa-circle"
            color = "secondary"

        step_items.append(
            html.Div([
                html.Div([
                    html.I(className=icon)
                ], className=f"rounded-circle bg-{color} text-white d-flex align-items-center justify-content-center",
                   style={"width": "32px", "height": "32px", "fontSize": "14px"}),
                html.Span(step, className=f"text-{color} fw-{'bold' if is_current else 'normal'} small mt-1")
            ], className="d-flex flex-column align-items-center text-center")
        )

        # Add connector line (except for last step)
        if i < len(steps) - 1:
            step_items.append(
                html.Div(
                    className=f"flex-grow-1 border-top border-2 border-{color if is_completed else 'secondary'}",
                    style={"height": "2px", "margin": "16px 8px 0 8px"}
                )
            )

    return html.Div(
        step_items,
        className="d-flex align-items-start justify-content-between w-100 mb-4"
    )

def create_enhanced_loading_overlay(content, is_loading: bool = True,
                                  loading_text: str = "Loading...",
                                  spinner_size: str = "md"):
    """Create an enhanced loading overlay with better animations."""
    if not is_loading:
        return content

    spinner_classes = {
        "sm": "spinner-border-sm",
        "md": "",
        "lg": "spinner-border spinner-border-lg"
    }

    overlay = html.Div([
        html.Div([
            html.Div([
                html.Div(className=f"spinner-border text-primary {spinner_classes.get(spinner_size, '')}"),
                html.P(loading_text, className="mt-3 mb-0 text-muted")
            ], className="text-center")
        ], className="d-flex align-items-center justify-content-center h-100 bg-white bg-opacity-90")
    ], style={
        "position": "absolute",
        "top": "0",
        "left": "0",
        "right": "0",
        "bottom": "0",
        "z-index": "1000",
        "border-radius": "0.5rem"
    })

    return html.Div([
        content,
        overlay
    ], style={"position": "relative", "min-height": "200px"})
