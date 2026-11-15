/*
 * XlinOS init (PID 1) with a tiny built-in shell.
 * First building block of XlinOS: everything here is our own code.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <signal.h>
#include <unistd.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/sysinfo.h>
#include <sys/utsname.h>
#include <sys/wait.h>

#ifndef XLIN_VERSION
#define XLIN_VERSION "dev"
#endif

#define OK   "\033[1;32m[  OK  ]\033[0m "
#define FAIL "\033[1;31m[FAILED]\033[0m "

static int is_init;

static void banner(void)
{
	printf("\n  __  __ _ _         ___  ____\n"
	       "  \\ \\/ /| (_)_ __   / _ \\/ ___|\n"
	       "   \\  / | | | '_ \\ | | | \\___ \\\n"
	       "   /  \\ | | | | | || |_| |___) |\n"
	       "  /_/\\_\\|_|_|_| |_| \\___/|____/\n\n"
	       "  XlinOS %s\n  Type 'help' for commands.\n\n", XLIN_VERSION);
}

static void step(const char *what, int rc)
{
	printf("%s%s\n", rc ? FAIL : OK, what);
}

static void setup_system(void)
{
	mkdir("/proc", 0555);
	mkdir("/sys", 0555);
	mkdir("/dev", 0755);
	mkdir("/tmp", 01777);
	step("Mounted /proc", mount("proc", "/proc", "proc", 0, NULL));
	step("Mounted /sys", mount("sysfs", "/sys", "sysfs", 0, NULL));
	step("Mounted /dev", mount("devtmpfs", "/dev", "devtmpfs", 0, NULL));
	step("Mounted /tmp", mount("tmpfs", "/tmp", "tmpfs", 0, NULL));
	step("Set hostname to xlin", sethostname("xlin", 4));
}

static void cmd_cat(const char *path)
{
	FILE *f = fopen(path, "r");
	char buf[512];
	size_t n;

	if (!f) {
		printf("cat: %s: %s\n", path, strerror(errno));
		return;
	}
	while ((n = fread(buf, 1, sizeof buf, f)) > 0)
		fwrite(buf, 1, n, stdout);
	fclose(f);
}

static void cmd_ls(const char *path)
{
	DIR *d = opendir(path ? path : ".");
	struct dirent *e;

	if (!d) {
		printf("ls: %s: %s\n", path ? path : ".", strerror(errno));
		return;
	}
	while ((e = readdir(d)))
		if (e->d_name[0] != '.')
			printf("%s%s\n", e->d_name, e->d_type == DT_DIR ? "/" : "");
	closedir(d);
}

static void cmd_info(void)
{
	struct utsname u;
	struct sysinfo si;

	uname(&u);
	sysinfo(&si);
	printf("XlinOS %s\nkernel  : %s\nmachine : %s\nhost    : %s\n"
	       "uptime  : %lds\nmemory  : %lu / %lu MiB free\n",
	       XLIN_VERSION, u.release, u.machine, u.nodename, si.uptime,
	       si.freeram * si.mem_unit >> 20, si.totalram * si.mem_unit >> 20);
}

static void run_line(char *line)
{
	char *cmd = strtok(line, " \t\n");
	char *arg = strtok(NULL, "\n");

	if (!cmd)
		return;
	if (!strcmp(cmd, "help"))
		puts("help info ls [dir] cat <file> echo <text> clear reboot poweroff");
	else if (!strcmp(cmd, "info"))
		cmd_info();
	else if (!strcmp(cmd, "ls"))
		cmd_ls(arg);
	else if (!strcmp(cmd, "cat"))
		arg ? cmd_cat(arg) : puts("usage: cat <file>");
	else if (!strcmp(cmd, "echo"))
		puts(arg ? arg : "");
	else if (!strcmp(cmd, "clear"))
		fputs("\033[2J\033[H", stdout);
	else if (!strcmp(cmd, "reboot")) {
		sync();
		if (is_init)
			reboot(RB_AUTOBOOT);
		puts("reboot: only works as init");
	} else if (!strcmp(cmd, "poweroff")) {
		sync();
		if (is_init)
			reboot(RB_POWER_OFF);
		puts("poweroff: only works as init");
	} else
		printf("xlin: command not found: %s\n", cmd);
}

static void reap(int sig)
{
	(void)sig;
	while (waitpid(-1, NULL, WNOHANG) > 0)
		;
}

int main(void)
{
	char line[256];

	is_init = getpid() == 1;
	if (is_init) {
		setup_system();
		signal(SIGCHLD, reap);
	}
	setvbuf(stdout, NULL, _IONBF, 0);
	banner();
	for (;;) {
		fputs("\033[1;36mroot@xlin\033[0m:\033[1;34m~\033[0m# ", stdout);
		if (!fgets(line, sizeof line, stdin)) {
			if (!is_init)
				break;
			clearerr(stdin);
			sleep(1);
			continue;
		}
		run_line(line);
	}
	return 0;
}
